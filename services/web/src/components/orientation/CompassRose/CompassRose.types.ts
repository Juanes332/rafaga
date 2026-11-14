export interface CompassRoseProps {
  /** Rendered width and height in px. */
  size?: number;
  /** Clockwise turn of north away from the top of the view, in degrees. */
  rotationDeg?: number;
  /** Replaces the default accessible name. */
  label?: string;
  className?: string;
}
