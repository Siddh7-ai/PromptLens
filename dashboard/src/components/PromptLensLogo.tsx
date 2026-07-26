import React from 'react';

interface PromptLensLogoProps {
  className?: string;
}

export const PromptLensLogo: React.FC<PromptLensLogoProps> = ({ className = 'w-full h-full object-contain' }) => {
  return (
    <img
      src="/logo.png"
      alt="PromptLens Logo"
      className={className}
    />
  );
};
