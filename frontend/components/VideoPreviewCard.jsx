'use client';

import React, { useEffect, useMemo, useState } from 'react';

const YOUTUBE_ID_PATTERN = /^[a-zA-Z0-9_-]{11}$/;

/**
 * Extract the 11-character YouTube video ID from common YouTube URL formats.
 * Supports youtube.com/watch?v=, youtu.be/, /embed/, /shorts/, and raw IDs.
 */
export function extractVideoId(url) {
  if (!url || typeof url !== 'string') return null;

  const value = url.trim();
  if (YOUTUBE_ID_PATTERN.test(value)) return value;

  try {
    const parsedUrl = new URL(value.startsWith('http') ? value : `https://${value}`);
    const host = parsedUrl.hostname.replace(/^www\./, '').replace(/^m\./, '');

    if (host === 'youtu.be') {
      const id = parsedUrl.pathname.split('/').filter(Boolean)[0];
      return YOUTUBE_ID_PATTERN.test(id) ? id : null;
    }

    if (host === 'youtube.com' || host === 'youtube-nocookie.com') {
      const watchId = parsedUrl.searchParams.get('v');
      if (YOUTUBE_ID_PATTERN.test(watchId)) return watchId;

      const pathParts = parsedUrl.pathname.split('/').filter(Boolean);
      const idFromPath = ['embed', 'shorts', 'v', 'e'].includes(pathParts[0]) ? pathParts[1] : null;
      return YOUTUBE_ID_PATTERN.test(idFromPath) ? idFromPath : null;
    }
  } catch {
    const fallbackMatch = value.match(/(?:v=|youtu\.be\/|embed\/|shorts\/|\/v\/|\/e\/)([a-zA-Z0-9_-]{11})/);
    return fallbackMatch ? fallbackMatch[1] : null;
  }

  return null;
}

export default function VideoPreviewCard({
  url,
  title = 'Video Preview',
  description = 'Ready for AI summarization',
  className = '',
}) {
  const [thumbnailQuality, setThumbnailQuality] = useState('maxresdefault');
  const [isLoading, setIsLoading] = useState(Boolean(url));
  const [thumbnailUnavailable, setThumbnailUnavailable] = useState(false);

  const videoId = useMemo(() => extractVideoId(url), [url]);
  const hasUrl = Boolean(url && url.trim());
  const hasInvalidUrl = hasUrl && !videoId;
  const thumbnailUrl = videoId
    ? `https://img.youtube.com/vi/${videoId}/${thumbnailQuality}.jpg`
    : '';
  const youtubeUrl = videoId ? `https://www.youtube.com/watch?v=${videoId}` : '#';

  useEffect(() => {
    setThumbnailQuality('maxresdefault');
    setThumbnailUnavailable(false);
    setIsLoading(Boolean(videoId));
  }, [videoId]);

  function handleImageError() {
    if (thumbnailQuality === 'maxresdefault') {
      setThumbnailQuality('hqdefault');
      setIsLoading(true);
      return;
    }

    setIsLoading(false);
    setThumbnailUnavailable(true);
  }

  function handleImageLoad(event) {
    const imageLooksUnavailable = event.currentTarget.naturalWidth <= 120;

    if (imageLooksUnavailable && thumbnailQuality === 'maxresdefault') {
      setThumbnailQuality('hqdefault');
      setIsLoading(true);
      return;
    }

    if (imageLooksUnavailable) {
      setThumbnailUnavailable(true);
    }

    setIsLoading(false);
  }

  if (!hasUrl) return null;

  return (
    <article
      className={`group overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950/90 shadow-2xl shadow-black/30 transition-all duration-300 hover:-translate-y-0.5 hover:border-purple-500/40 hover:shadow-purple-500/10 ${className}`}
    >
      <div className="relative aspect-video overflow-hidden bg-zinc-900">
        {isLoading && !hasInvalidUrl && !thumbnailUnavailable && (
          <div className="absolute inset-0 animate-pulse bg-zinc-900">
            <div className="h-full w-full bg-gradient-to-r from-zinc-900 via-zinc-800 to-zinc-900" />
          </div>
        )}

        {videoId && !thumbnailUnavailable && (
          <img
            src={thumbnailUrl}
            alt={`${title} thumbnail`}
            className={`h-full w-full object-cover transition duration-500 group-hover:scale-105 ${
              isLoading ? 'opacity-0' : 'opacity-100'
            }`}
            onLoad={handleImageLoad}
            onError={handleImageError}
          />
        )}

        {(hasInvalidUrl || thumbnailUnavailable) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900 px-6 text-center">
            <p className="text-sm font-semibold text-zinc-100">
              {hasInvalidUrl ? 'Invalid YouTube URL' : 'Thumbnail unavailable'}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              {hasInvalidUrl
                ? 'Paste a valid YouTube watch, short, or share link.'
                : 'The video can still be opened on YouTube.'}
            </p>
          </div>
        )}
      </div>

      <div className="space-y-4 p-5">
        <div>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <p className="mt-1 text-sm text-zinc-400">{description}</p>
        </div>

        <a
          href={youtubeUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-disabled={!videoId}
          className={`inline-flex w-full items-center justify-center rounded-xl border px-4 py-2.5 text-sm font-semibold transition ${
            videoId
              ? 'border-zinc-700 bg-zinc-900 text-zinc-100 hover:border-purple-500/50 hover:bg-zinc-800'
              : 'pointer-events-none border-zinc-800 bg-zinc-900/60 text-zinc-600'
          }`}
        >
          Open on YouTube
        </a>
      </div>
    </article>
  );
}
