import { z } from "zod";

export const emailSchema = z.string().trim().email("Enter a valid email address");

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(128, "Password is too long")
  .regex(/[0-9]/, "Password must contain a digit")
  .regex(/[a-zA-Z]/, "Password must contain a letter");

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    name: z.string().trim().min(1, "Name is required").max(120),
    email: emailSchema,
    password: passwordSchema,
    confirm: z.string(),
  })
  .refine((data) => data.password === data.confirm, { path: ["confirm"], message: "Passwords do not match" });
export type RegisterInput = z.infer<typeof registerSchema>;

export const tagSchema = z
  .string()
  .trim()
  .toLowerCase()
  .transform((value) => value.replace(/\s+/g, "-"))
  .pipe(z.string().regex(/^[a-z0-9][a-z0-9\-_]{0,48}$/, "Tags may contain letters, numbers, hyphens and underscores"));

export const noteSchema = z.object({
  title: z.string().trim().min(1, "Title is required").max(200, "Title is too long"),
  content: z.string().max(100_000, "Note is too long"),
  notebook_id: z.string().nullable().optional(),
  tags: z.array(tagSchema).max(20, "At most 20 tags"),
});
export type NoteInput = z.infer<typeof noteSchema>;

export const notebookSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(120),
  description: z.string().trim().max(2000).optional(),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Pick a colour"),
});
export type NotebookFormInput = z.infer<typeof notebookSchema>;

export const profileSchema = z
  .object({
    name: z.string().trim().min(1, "Name is required").max(120),
    current_password: z.string().optional(),
    new_password: z.union([z.literal(""), passwordSchema]).optional(),
  })
  .refine((data) => !data.new_password || Boolean(data.current_password), {
    path: ["current_password"],
    message: "Enter your current password to change it",
  });
export type ProfileInput = z.infer<typeof profileSchema>;

/** Flatten a zod error into { field: message }. */
export function fieldErrors(error: z.ZodError): Record<string, string> {
  const result: Record<string, string> = {};
  for (const issue of error.issues) {
    const key = issue.path.join(".") || "_";
    if (!result[key]) result[key] = issue.message;
  }
  return result;
}
