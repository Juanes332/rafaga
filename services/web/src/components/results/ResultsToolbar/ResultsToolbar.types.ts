export interface DirectionOption {
  resultId: string;
  label: string;
}

export interface ResultsToolbarProps {
  resultId: string;
  kind: "plan2d" | "section2d" | "volume3d";
  directions: DirectionOption[];
  readOnly: boolean;
  onDirection: (resultId: string) => void;
}
