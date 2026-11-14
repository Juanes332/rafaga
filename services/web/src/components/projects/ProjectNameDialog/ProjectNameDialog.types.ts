export interface ProjectNameDialogProps {
  open: boolean;
  title: string;
  submitLabel: string;
  initialName?: string;
  pending: boolean;
  error: unknown;
  onOpenChange: (open: boolean) => void;
  onSubmit: (name: string) => void;
}
