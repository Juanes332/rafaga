export interface GeometryToolbarProps {
  readOnly: boolean;
  saving: boolean;
  checking: boolean;
  onSave: () => void;
  onCheck: () => void;
  onImport: () => void;
  onTrace: () => void;
}
