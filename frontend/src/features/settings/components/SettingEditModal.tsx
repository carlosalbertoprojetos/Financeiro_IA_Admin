"use client";

import type { ReactNode } from "react";

import { Modal } from "@/shared/ui";

interface SettingEditModalProps {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  onSubmit: () => void;
  submitting?: boolean;
  submitLabel?: string;
  children: ReactNode;
}

export function SettingEditModal({
  open,
  title,
  description,
  onClose,
  onSubmit,
  submitting = false,
  submitLabel = "Salvar",
  children,
}: SettingEditModalProps) {
  return (
    <Modal
      open={open}
      title={title}
      description={description}
      titleId="setting-edit-title"
      onClose={onClose}
      onSubmit={onSubmit}
      submitting={submitting}
      submitLabel={submitLabel}
    >
      {children}
    </Modal>
  );
}
