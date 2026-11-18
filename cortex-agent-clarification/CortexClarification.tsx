"use client";

import React, { useState } from "react";

export interface ClarificationOption {
  label: string;
  description?: string;
}

export interface ClarificationEvent {
  question: string;
  options: ClarificationOption[];
  allowSkip?: boolean;
}

interface CortexClarificationProps {
  clarification: ClarificationEvent;
  onSubmit: (selectedOption: string) => void;
  onSkip?: () => void;
}

export function CortexClarification({
  clarification,
  onSubmit,
  onSkip,
}: CortexClarificationProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [customText, setCustomText] = useState("");
  const [showCustom, setShowCustom] = useState(false);

  const handleSubmit = () => {
    if (showCustom && customText.trim()) {
      onSubmit(customText.trim());
    } else if (selected) {
      onSubmit(selected);
    }
  };

  return (
    <div className="cortex-clarification">
      <p className="cortex-clarification__question">{clarification.question}</p>

      <div className="cortex-clarification__options">
        {clarification.options.map((option, idx) => (
          <label
            key={idx}
            className={`cortex-clarification__option ${
              selected === option.label ? "cortex-clarification__option--selected" : ""
            }`}
          >
            <input
              type="radio"
              name="clarification"
              value={option.label}
              checked={selected === option.label && !showCustom}
              onChange={() => {
                setSelected(option.label);
                setShowCustom(false);
              }}
            />
            <div className="cortex-clarification__option-content">
              <span className="cortex-clarification__option-label">{option.label}</span>
              {option.description && (
                <span className="cortex-clarification__option-desc">
                  {option.description}
                </span>
              )}
            </div>
          </label>
        ))}

        {/* "Something else..." option */}
        <label
          className={`cortex-clarification__option ${
            showCustom ? "cortex-clarification__option--selected" : ""
          }`}
        >
          <input
            type="radio"
            name="clarification"
            checked={showCustom}
            onChange={() => {
              setShowCustom(true);
              setSelected(null);
            }}
          />
          <div className="cortex-clarification__option-content">
            <span className="cortex-clarification__option-label">Something else...</span>
          </div>
        </label>

        {showCustom && (
          <input
            type="text"
            className="cortex-clarification__custom-input"
            placeholder="Type your response..."
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            autoFocus
          />
        )}
      </div>

      <div className="cortex-clarification__actions">
        <button
          className="cortex-clarification__btn cortex-clarification__btn--submit"
          onClick={handleSubmit}
          disabled={!selected && !(showCustom && customText.trim())}
        >
          Submit
        </button>
        {(clarification.allowSkip ?? true) && onSkip && (
          <button
            className="cortex-clarification__btn cortex-clarification__btn--skip"
            onClick={onSkip}
          >
            Skip
          </button>
        )}
      </div>
    </div>
  );
}
