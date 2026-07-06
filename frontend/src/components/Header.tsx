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
          <span className="brand-letter bg-[#1C3BFF] text-white">P</span>
          <span className="brand-letter bg-[#FFA000] text-black">R</span>
          <span className="brand-letter bg-[#FF1CAE] text-white">O</span>
          <span className="brand-letter bg-[#E0FF1C] text-black">M</span>
          <span className="brand-letter bg-[#1CFF3B] text-black">P</span>
          <span className="brand-letter bg-[#111111] text-white">T</span>
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
          className="brutal-btn header-btn bg-[#FFA000]"
          title="How to Play"
        >
          <HelpCircle size={20} />
        </button>

        <button
          onClick={onOpenAbout}
          className="brutal-btn header-btn bg-[#1CFF3B]"
          title="About Game"
        >
          <Info size={20} />
        </button>

        <button
          onClick={onOpenSettings}
          className="brutal-btn header-btn bg-[#FF1CAE]"
          title="Settings"
        >
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
};
