"""
Comprehensive fix for MoE models with missing expert weights.
This script ensures all experts exist with proper weights for GGUF conversion.
"""

import json
import os
import shutil
from pathlib import Path
from safetensors.torch import load_file, save_file
from collections import defaultdict
import torch

def analyze_expert_structure(model_dir):
    """Analyze the expert structure and find all issues"""
    print("Analyzing model structure...")
    
    index_path = Path(model_dir) / "model.safetensors.index.json"
    with open(index_path, 'r') as f:
        index_data = json.load(f)
    
    weight_map = index_data['weight_map']
    
    # Find all expert-related weights
    expert_weights = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    for key in weight_map.keys():
        if 'mlp.experts' in key:
            parts = key.split('.')
            layer_idx = int(parts[2])
            expert_idx = int(parts[5])
            proj_type = parts[6]  # gate_proj, up_proj, down_proj
            weight_type = parts[7] if len(parts) > 7 else 'weight'  # weight or bias
            
            expert_weights[layer_idx][proj_type][expert_idx][weight_type] = {
                'key': key,
                'shard': weight_map[key]
            }
    
    return expert_weights, index_data, weight_map

def find_missing_experts(expert_weights):
    """Find missing experts across all layers"""
    issues = []
    
    for layer_idx in sorted(expert_weights.keys()):
        layer_data = expert_weights[layer_idx]
        
        # Get all projection types in this layer
        proj_types = list(layer_data.keys())
        if not proj_types:
            continue
        
        # Find the maximum number of experts across all projection types
        all_expert_indices = set()
        for proj_type in proj_types:
            all_expert_indices.update(layer_data[proj_type].keys())
        
        if not all_expert_indices:
            continue
            
        max_expert = max(all_expert_indices)
        expected_experts = set(range(max_expert + 1))
        
        # Check each projection type
        for proj_type in ['gate_proj', 'up_proj', 'down_proj']:
            if proj_type not in layer_data:
                print(f"  Warning: Layer {layer_idx} missing entire {proj_type}")
                continue
                
            actual_experts = set(layer_data[proj_type].keys())
            missing = expected_experts - actual_experts
            
            if missing:
                # Find a source expert to copy from
                available = sorted(actual_experts)
                if available:
                    issues.append({
                        'layer': layer_idx,
                        'proj_type': proj_type,
                        'missing': sorted(missing),
                        'source_expert': available[0]
                    })
    
    return issues

def fix_model(model_dir, issues, expert_weights, index_data, weight_map):
    """Fix the model by adding missing expert weights"""
    print(f"\nFixing {len(issues)} issues...")
    
    model_dir = Path(model_dir)
    
    # Create backups
    backup_dir = model_dir / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    # Group modifications by shard
    shard_mods = defaultdict(list)
    
    for issue in issues:
        layer = issue['layer']
        proj_type = issue['proj_type']
        source_expert = issue['source_expert']
        
        for missing_expert in issue['missing']:
            # Get source weights
            if source_expert not in expert_weights[layer][proj_type]:
                print(f"  Warning: Source expert {source_expert} not found for layer {layer}")
                continue
            
            source_info = expert_weights[layer][proj_type][source_expert]
            
            for weight_type, info in source_info.items():
                source_key = info['key']
                shard_file = info['shard']
                
                # Generate target key
                target_key = f"model.layers.{layer}.mlp.experts.{missing_expert}.{proj_type}.{weight_type}"
                
                shard_mods[shard_file].append({
                    'source': source_key,
                    'target': target_key,
                    'layer': layer,
                    'proj': proj_type,
                    'expert': missing_expert
                })
    
    # Process each shard
    for shard_file, mods in shard_mods.items():
        shard_path = model_dir / shard_file
        print(f"\nProcessing {shard_file}...")
        
        # Backup
        backup_path = backup_dir / shard_file
        if not backup_path.exists():
            shutil.copy2(shard_path, backup_path)
            print(f"  Backed up to {backup_path}")
        
        # Load weights
        print(f"  Loading {len(mods)} modifications...")
        weights = load_file(str(shard_path))
        
        # Apply modifications
        added = 0
        for mod in mods:
            source_key = mod['source']
            target_key = mod['target']
            
            if source_key in weights:
                if target_key not in weights:
                    # Clone the tensor to avoid sharing memory
                    weights[target_key] = weights[source_key].clone()
                    weight_map[target_key] = shard_file
                    added += 1
                    print(f"    Added: layer {mod['layer']}, expert {mod['expert']}, {mod['proj']}")
            else:
                print(f"    ERROR: Source not found: {source_key}")
        
        # Save modified shard
        if added > 0:
            print(f"  Saving {added} new weights...")
            save_file(weights, str(shard_path))
        
    # Update index
    index_path = model_dir / "model.safetensors.index.json"
    index_backup = backup_dir / "model.safetensors.index.json"
    
    if not index_backup.exists():
        shutil.copy2(index_path, index_backup)
    
    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"\n✅ Model fixed! Backups saved to {backup_dir}")

def verify_fix(model_dir):
    """Verify the fix worked"""
    print("\nVerifying fix...")
    expert_weights, _, _ = analyze_expert_structure(model_dir)
    issues = find_missing_experts(expert_weights)
    
    if issues:
        print(f"❌ Still have {len(issues)} issues!")
        return False
    else:
        print("✅ All experts present! Model ready for conversion.")
        return True

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fix_moe_model.py <model_directory>")
        print("\nExample:")
        print("  python fix_moe_model.py /path/to/fused_model")
        sys.exit(1)
    
    model_dir = sys.argv[1]
    
    if not os.path.exists(model_dir):
        print(f"Error: Directory not found: {model_dir}")
        sys.exit(1)
    
    print("=" * 70)
    print("MoE MODEL FIX TOOL")
    print("=" * 70)
    
    # Analyze
    expert_weights, index_data, weight_map = analyze_expert_structure(model_dir)
    issues = find_missing_experts(expert_weights)
    
    if not issues:
        print("\n✅ No issues found! Model is ready for conversion.")
        print(f"\nRun: python convert_hf_to_gguf.py {model_dir}")
        return
    
    print(f"\n❌ Found {len(issues)} issues:")
    for issue in issues[:10]:  # Show first 10
        print(f"  Layer {issue['layer']}, {issue['proj_type']}: "
              f"missing experts {issue['missing']}")
    
    if len(issues) > 10:
        print(f"  ... and {len(issues) - 10} more")
    
    # Confirm fix
    print("\n" + "=" * 70)
    response = input("Fix these issues? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Fix
    fix_model(model_dir, issues, expert_weights, index_data, weight_map)
    
    # Verify
    if verify_fix(model_dir):
        print("\n" + "=" * 70)
        print("SUCCESS! Now run:")
        print(f"python convert_hf_to_gguf.py {model_dir}")
        print("=" * 70)

if __name__ == "__main__":
    main()