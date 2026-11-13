"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { resetPassword } from "@/lib/api/auth";

interface FormState {
  password: string;
  confirmPassword: string;
}

type FieldErrors = Partial<Record<keyof FormState, string>>;

function validate(form: FormState): FieldErrors {
  const errors: FieldErrors = {};
  if (!form.password) {
    errors.password = "Password is required.";
  } else if (form.password.length < 8) {
    errors.password = "Password must be at least 8 characters.";
  } else if (form.password.length > 72) {
    errors.password = "Password must be at most 72 characters.";
  }
  if (form.confirmPassword !== form.password) {
    errors.confirmPassword = "Passwords do not match.";
  }
  return errors;
}

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";

  const [form, setForm] = useState<FormState>({
    password: "",
    confirmPassword: "",
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const setField = (field: keyof FormState) => (value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    setServerError("");
  };

  if (!token) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold tracking-tight">Invalid reset link</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            This link is missing its reset token. Request a new email to continue.
          </p>
        </div>
        <Button className="w-full" render={<Link href="/forgot-password" />}>
          Request a new link
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          <Link
            href="/login"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Back to sign in
          </Link>
        </p>
      </div>
    );
  }

  if (done) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold tracking-tight">Password updated</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Your password has been reset. Sign in with your new password.
          </p>
        </div>
        <Button className="w-full" render={<Link href="/login" />}>
          Sign in
        </Button>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError("");

    const errors = validate(form);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      await resetPassword(token, form.password);
      setDone(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError("Something went wrong. Please try again.");
      }
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-semibold tracking-tight">Choose a new password</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter a new password for your account
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {serverError && (
          <div
            role="alert"
            className="rounded-lg border border-ember/25 bg-ember-dim/40 px-3 py-2 text-sm text-ember"
          >
            {serverError}{" "}
            <Link
              href="/forgot-password"
              className="font-medium underline underline-offset-4"
            >
              Request a new link
            </Link>
          </div>
        )}
        <div className="space-y-2">
          <Label htmlFor="password">New password</Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={form.password}
            onChange={(e) => setField("password")(e.target.value)}
            aria-invalid={Boolean(fieldErrors.password)}
            autoComplete="new-password"
          />
          {fieldErrors.password && (
            <p className="text-xs text-ember">{fieldErrors.password}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirmPassword">Confirm new password</Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="••••••••"
            value={form.confirmPassword}
            onChange={(e) => setField("confirmPassword")(e.target.value)}
            aria-invalid={Boolean(fieldErrors.confirmPassword)}
            autoComplete="new-password"
          />
          {fieldErrors.confirmPassword && (
            <p className="text-xs text-ember">{fieldErrors.confirmPassword}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Resetting..." : "Reset password"}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        <Link
          href="/login"
          className="font-medium text-primary underline-offset-4 hover:underline"
        >
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <p className="py-8 text-center text-sm text-muted-foreground">Loading...</p>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  );
}
