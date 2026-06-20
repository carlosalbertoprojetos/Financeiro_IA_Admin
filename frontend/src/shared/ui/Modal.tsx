"use client";

import type { ReactNode } from "react";

import { Button } from "./Button";

interface ModalProps {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  submitLabel?: string;
  onSubmit?: () => void;
  submitting?: boolean;
  titleId?: string;
}

export function Modal({
  open,
  title,
  description,
  onClose,
  children,
  footer,
  submitLabel = "Salvar",
  onSubmit,
  submitting = false,
  titleId = "modal-title",
}: ModalProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-overlay/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
    >
      <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-xl">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id={titleId} className="text-lg font-semibold text-foreground">
              {title}
            </h2>
            {description ? (
              <p className="mt-1 text-sm text-muted-foreground">{description}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-muted hover:bg-surface-muted hover:text-foreground"
            aria-label="Fechar"
          >
            ✕
          </button>
        </div>

        <div className="mt-5">{children}</div>

        {footer ?? (
          onSubmit ? (
            <div className="mt-6 flex flex-wrap gap-3">
              <Button onClick={onSubmit} disabled={submitting}>
                {submitting ? "Salvando…" : submitLabel}
              </Button>
              <Button variant="secondary" onClick={onClose}>
                Cancelar
              </Button>
            </div>
          ) : null
        )}
      </div>
    </div>
  );
}
