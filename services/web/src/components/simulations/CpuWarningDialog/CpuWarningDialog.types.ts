export interface CpuWarningDialogProps {
  open: boolean;
  etaSeconds: number;
  nodes: number;
  onCancel: () => void;
  onConfirm: () => void;
}
