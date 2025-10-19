'use client';

import { useExperiment, useStatsigClient } from "@statsig/react-bindings";

export default function Home() {
  const { client } = useStatsigClient();
  const experimentName = "test";
  const experiment = useExperiment(experimentName);
  const buttonColor = experiment.get('button_color', 'green');
  const buttonText = experiment.get('button_text', 'buy noww');

  const handleClick = () => {
    client.logEvent("button_clicked", experimentName, {
      button_color: buttonColor,
      button_text: buttonText,
    });
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <button
        onClick={handleClick}
        className="rounded-full px-8 py-4 text-white font-semibold text-lg hover:opacity-80 transition-opacity"
        style={{ backgroundColor: buttonColor }}
      >
        {buttonText}
      </button>
    </div>
  );
}