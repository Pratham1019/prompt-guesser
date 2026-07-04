import React from 'react';
import { HelpCircle, Settings, Info, Award } from 'lucide-react';

interface HeaderProps {
  onOpenHelp: () => void;
  onOpenAbout: () => void;
  onOpenSettings: () => void;
  bestScore: number;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenHelp,
  onOpenAbout,
  onOpenSettings,
  bestScore,
}) => {
  return (
    <header className="header-bar brutal-shadow">
      <div className="header-brand">
        <h1>
          <span className="bg-[#1C3BFF] text-white px-2 py-1 brutal-border-sm">P</span>
          <span className="bg-[#FFA000] text-black px-2 py-1 brutal-border-sm">R</span>
          <span className="bg-[#FF1CAE] text-white px-2 py-1 brutal-border-sm">O</span>
          <span className="bg-[#E0FF1C] text-black px-2 py-1 brutal-border-sm">M</span>
          <span className="bg-[#1CFF3B] text-black px-2 py-1 brutal-border-sm">P</span>
          <span className="bg-[#111111] text-white px-2 py-1 brutal-border-sm">T</span>
          <span className="header-brand-text">Guesser</span>
        </h1>
      </div>

      <div className="header-actions">
        {bestScore > 0 && (
          <div className="best-score-badge badge-brutal bg-[#E0FF1C]">
            <Award size={16} />
            <span>Best Score: {bestScore}%</span>
          </div>
        )}

        <button
          onClick={onOpenHelp}
          className="brutal-btn w-12 h-12 brutal-shadow bg-[#FFA000]"
          title="How to Play"
        >
          <HelpCircle size={20} />
        </button>

        <button
          onClick={onOpenAbout}
          className="brutal-btn w-12 h-12 brutal-shadow bg-[#1CFF3B]"
          title="About Game"
        >
          <Info size={20} />
        </button>

        <button
          onClick={onOpenSettings}
          className="brutal-btn w-12 h-12 brutal-shadow bg-[#FF1CAE]"
          title="Settings"
        >
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
};
