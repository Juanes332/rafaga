export interface ParamFieldProps {
  id: string;
  label: string;
  value: number | null;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  decimals?: number;
  defaultValue?: number | null;
  /** Definition, range and default in plain words; shown on hover and focus. */
  help?: string;
  slider?: boolean;
  /** Displays a 0..1 value as a percentage. */
  percent?: boolean;
  /** Message shown when the API clamped the value. */
  adjustment?: string | null;
  disabled?: boolean;
  onCommit: (value: number) => void;
}
