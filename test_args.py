#!/usr/bin/env python3
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='DPO LoRA Fine-tuning Script')
    parser.add_argument('--dataset-name', 
                       type=str, 
                       default="BOSSrobot343/dubhacks-buy_button",
                       help='Name of the dataset to use for training (default: BOSSrobot343/dubhacks-buy_button)')
    parser.add_argument('--model-name',
                       type=str,
                       default=None,
                       help='Name for the output model (default: uses timestamp)')
    
