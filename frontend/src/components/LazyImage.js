import { useState, useRef, useEffect } from 'react';

/**
 * LazyImage Component
 * Loads images only when they enter the viewport
 * Supports placeholder, error fallback, and loading states
 */
export default function LazyImage({ 
  src, 
  alt = '', 
  className = '', 
  placeholderClassName = '',
  errorFallback = null,
  threshold = 0.1,
  rootMargin = '100px',
  ...props 
}) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold, rootMargin }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [threshold, rootMargin]);

  const handleLoad = () => {
    setIsLoaded(true);
  };

  const handleError = () => {
    setHasError(true);
    setIsLoaded(true);
  };

  if (hasError && errorFallback) {
    return errorFallback;
  }

  return (
    <div 
      ref={imgRef} 
      className={`relative overflow-hidden ${placeholderClassName}`}
      style={{ minHeight: props.height || '100px' }}
    >
      {/* Placeholder skeleton */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-slate-200 animate-pulse flex items-center justify-center">
          <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      )}
      
      {/* Actual image - only load src when in view */}
      {isInView && (
        <img
          src={src}
          alt={alt}
          className={`${className} transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={handleLoad}
          onError={handleError}
          loading="lazy"
          decoding="async"
          {...props}
        />
      )}
      
      {/* Error state */}
      {hasError && !errorFallback && (
        <div className="absolute inset-0 bg-slate-100 flex items-center justify-center text-slate-400">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
      )}
    </div>
  );
}

/**
 * LazyImageGrid Component
 * Efficiently renders a grid of images with lazy loading
 */
export function LazyImageGrid({ 
  images, 
  columns = 4, 
  gap = 4,
  onImageClick,
  imageClassName = '',
  containerClassName = ''
}) {
  return (
    <div 
      className={`grid gap-${gap} ${containerClassName}`}
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
      {images.map((image, index) => (
        <div 
          key={image.id || index}
          className="cursor-pointer hover:opacity-90 transition-opacity"
          onClick={() => onImageClick?.(image, index)}
        >
          <LazyImage
            src={image.url || image.file_url || image.src}
            alt={image.title || image.name || `Image ${index + 1}`}
            className={`w-full h-auto object-cover rounded ${imageClassName}`}
            placeholderClassName="aspect-square rounded"
          />
          {image.title && (
            <p className="text-xs text-slate-600 mt-1 truncate">{image.title}</p>
          )}
        </div>
      ))}
    </div>
  );
}
