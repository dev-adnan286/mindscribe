"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth/hooks";
import { fieldErrors, registerSchema } from "@/lib/schemas";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const update = (field: keyof typeof form) => (event: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [field]: event.target.value }));

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = registerSchema.safeParse(form);
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      return;
    }
    setErrors({});
    setSubmitting(true);
    try {
      await register(parsed.data.email, parsed.data.password, parsed.data.name);
      router.replace("/app");
    } catch (error) {
      if (error instanceof ApiError) {
        const fields = error.fieldErrors;
        setErrors(Object.keys(fields).length ? fields : { _: error.message });
      } else {
        setErrors({ _: "Could not create your account. Please try again." });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-5" noValidate>
      <div>
        <h1 className="text-2xl font-bold">Create your account</h1>
        <p className="mt-1 text-sm text-slate-500">Free, private, and works offline with the built-in assistant.</p>
      </div>
      {errors._ && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {errors._}
        </p>
      )}
      <Input label="Name" autoComplete="name" value={form.name} onChange={update("name")} error={errors.name} required />
      <Input label="Email" type="email" autoComplete="email" value={form.email} onChange={update("email")} error={errors.email} required />
      <Input
        label="Password"
        type="password"
        autoComplete="new-password"
        value={form.password}
        onChange={update("password")}
        error={errors.password}
        hint="At least 8 characters with a letter and a digit."
        required
      />
      <Input
        label="Confirm password"
        type="password"
        autoComplete="new-password"
        value={form.confirm}
        onChange={update("confirm")}
        error={errors.confirm}
        required
      />
      <Button type="submit" className="w-full" loading={submitting}>
        Create account
      </Button>
      <p className="text-center text-sm text-slate-500">
        Already registered?{" "}
        <Link href="/login" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
          Sign in
        </Link>
      </p>
    </form>
  );
}
