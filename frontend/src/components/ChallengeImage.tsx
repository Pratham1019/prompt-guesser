import React, { useState } from 'react';
import { ImageIcon } from 'lucide-react';

interface ChallengeImageProps {
  imageUrl: string;
  loading: boolean;
  publishDate: string;
  imageToken?: number;
}

export const ChallengeImage: React.FC<ChallengeImageProps> = ({
  imageUrl,
  loading,
  publishDate,
  imageToken,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);

  if (loading) {
    return (
      <div className="brutal-skeleton challenge-image-wrapper flex-row-gap-2">
        <div className="flex-row-gap-2">
          <ImageIcon size={48} className="animate-pulse-brutal" />
          <span className="mono-label text-sm">Loading daily image...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="brutal-card challenge-image-card">
      {/* Date banner */}
      <div className="challenge-image-header">
        <span className="mono-label">Daily Image</span>
        <span className="mono-label">{publishDate}</span>
      </div>

      <div className="challenge-image-wrapper">
        {!imageLoaded && (
          <div className="brutal-skeleton flex-row-gap-2 animate-pulse-brutal" style={{ position: 'absolute', inset: 0, justifyContent: 'center' }}>
            <ImageIcon size={32} />
          </div>
        )}
        <img
          src={imageUrl ? `${imageUrl}?t=${imageToken || ''}` : ''}
          alt="Prompt Challenge Target"
          style={{ transition: 'opacity 0.3s ease', opacity: imageLoaded ? 1 : 0 }}
          onLoad={() => setImageLoaded(true)}
        />
      </div>
    </div>
  );
};
