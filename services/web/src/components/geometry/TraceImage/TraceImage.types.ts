export type Px = [number, number];

export interface TraceImageProps {
  url: string;
  alt: string;
  points: Px[];
  /** Click position in natural image pixels. */
  onPick: (p: Px) => void;
}
