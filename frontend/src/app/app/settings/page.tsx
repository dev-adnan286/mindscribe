"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";

import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useToast } from "@/components/Toast";
import { ApiError, aiApi, authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/hooks";
import { fieldErrors, profileSchema } from "@/lib/schemas";
import { formatDate } from "@/lib/utils";

export default function SettingsPage() {
  const { user, setUser } = useAuth();
  const toast = useToast();
  const [name, setName] = useState(user?.name ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const ai = useQuery({ queryKey: ["ai-status"], queryFn: aiApi.status });

  useEffect(() => {
    if (user) setName(user.name);
  }, [user]);

  const update = useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: (updated) => {
      setUser(updated);
      setCurrentPassword("");
      setNewPassword("");
      setErrors({});
      toast.success("Profile updated");
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        const fields = error.fieldErrors;
        setErrors(Object.keys(fields).length ? fields : { _: error.message });
      }
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const parsed = profileSchema.safeParse({ name, current_password: currentPassword, new_password: newPassword });
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    const payload: { name?: string; current_password?: string; new_password?: string } = {};
    if (parsed.data.name !== user?.name) payload.name = parsed.data.name;
    if (parsed.data.new_password) {
      payload.current_password = parsed.data.current_password;
      payload.new_password = parsed.data.new_password;
    }
    if (Object.keys(payload).length === 0) {
      toast.info("Nothing to update");
      return;
    }
    update.mutate(payload);
  };

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-slate-500">Manage your profile and see how the assistant is configured.</p>
      </div>

      <form onSubmit={submit} className="card space-y-5 p-6" noValidate>
        <h2 className="font-semibold">Profile</h2>
        {errors._ && (
          <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
            {errors._}
          </p>
        )}
        <Input label="Email" value={user?.email ?? ""} disabled hint="Email addresses cannot be changed." />
        <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} error={errors.name} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Current password"
            type="password"
            autoComplete="current-password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            error={errors.current_password}
          />
          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            error={errors.new_password}
            hint="Leave blank to keep your password. Changing it signs out other devices."
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">Member since {user ? formatDate(user.created_at) : ""}</span>
          <Button type="submit" loading={update.isPending}>
            Save changes
          </Button>
        </div>
      </form>

      <section className="card p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Appearance</h2>
          <ThemeToggle />
        </div>
        <p className="mt-1 text-sm text-slate-500">Toggle between light and dark mode. Your choice is remembered on this device.</p>
      </section>

      <section className="card p-6">
        <h2 className="font-semibold">AI configuration</h2>
        <p className="mt-1 text-sm text-slate-500">Configured on the server through environment variables.</p>
        {ai.data ? (
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <dt className="text-slate-500">Provider</dt>
            <dd>
              <Badge tone={ai.data.provider === "mock" ? "warning" : "success"}>{ai.data.provider}</Badge>
            </dd>
            <dt className="text-slate-500">Model</dt>
            <dd className="font-mono text-xs">{ai.data.model}</dd>
            <dt className="text-slate-500">Embeddings</dt>
            <dd>
              {ai.data.embedding_provider} ({ai.data.embedding_dim} dims)
            </dd>
          </dl>
        ) : (
          <p className="mt-3 text-sm text-slate-400">Loading...</p>
        )}
        {ai.data?.provider === "mock" && (
          <p className="mt-4 rounded-lg bg-amber-50 p-3 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
            The offline mock provider is active: summaries and tags use extractive heuristics. Set AI_PROVIDER to
            anthropic or openai on the backend for LLM-generated results.
          </p>
        )}
      </section>
    </div>
  );
}
