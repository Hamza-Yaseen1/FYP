import type { Metadata } from "next";
import Link from "next/link";
import {
  LegalList,
  LegalPageShell,
  LegalSection,
} from "@/components/marketing/LegalPageShell";
import { BRAND_NAME } from "@/lib/brand";
import { CONTACT_EMAIL } from "@/lib/site";

export const metadata: Metadata = {
  title: `Privacy Policy — ${BRAND_NAME}`,
  description: `How ${BRAND_NAME} collects, uses, stores, and protects account, message, and Google Gmail data.`,
};

const reviewNotes = [
  "Confirm the operator/legal entity name, postal address, and jurisdiction that should appear in this policy.",
  "Confirm retention periods for hosting/server logs and MongoDB Atlas backups — the application does not define these.",
  "Confirm the children's privacy age threshold that applies in your jurisdiction.",
  "Confirm whether you plan to add \"Sign in with Google\" for authentication. The current app uses email/password sign-in; Google OAuth is used only for the optional Gmail connection.",
  "Confirm that the Google API Limited Use statement below remains accurate for your deployment, and complete Google's OAuth verification for the restricted gmail.readonly scope.",
  "If you later add self-service account deletion or data export, update the rights section to describe it.",
];

export default function PrivacyPolicyPage() {
  return (
    <LegalPageShell
      title="Privacy Policy"
      summary={`This policy explains what ${BRAND_NAME} collects, why it is collected, how it is stored, and the choices you have. It is written to match the features that are actually implemented in this application.`}
      reviewNotes={reviewNotes}
    >
      <LegalSection id="who-we-are" title="Who we are">
        <p>
          {BRAND_NAME} is an academic Final Year Project (FYP) developed by Hamza
          Yaseen at BBSUL. It is a communication overload management tool that
          helps you prioritize messages, read AI-generated summaries, extract
          tasks, and review your communication activity in one place.
        </p>
        <p>
          In this policy, &quot;we&quot;, &quot;us&quot;, and &quot;our&quot;
          refer to the {BRAND_NAME} project. &quot;You&quot; means the person
          using the application.
        </p>
      </LegalSection>

      <LegalSection id="information-we-collect" title="Information we collect">
        <p>We collect the following categories of information:</p>
        <LegalList>
          <li>
            <span className="text-foreground">Account data:</span> your name,
            email address, a bcrypt password hash (never the plain password),
            and the date your account was created.
          </li>
          <li>
            <span className="text-foreground">Message data:</span> messages you
            add manually, receive through the WhatsApp webhook, or import from
            Gmail after you connect it. This can include sender name or address,
            subject, message content, source, timestamps, and external message
            identifiers.
          </li>
          <li>
            <span className="text-foreground">AI analysis data:</span> priority,
            confidence, explanation, summary, recommended actions, extracted
            tasks, and deadlines generated from your messages.
          </li>
          <li>
            <span className="text-foreground">Task data:</span> tasks extracted
            from messages or created by you, including status, priority, and due
            dates.
          </li>
          <li>
            <span className="text-foreground">Connection data:</span> if you
            connect Gmail, we store the connected Gmail address and encrypted
            OAuth access and refresh tokens.
          </li>
          <li>
            <span className="text-foreground">Session and technical data:</span>{" "}
            an authentication cookie, and standard server/hosting logs that may
            include IP address, browser type, timestamps, and error diagnostics.
          </li>
        </LegalList>
        <p>
          We do not use advertising trackers, third-party analytics scripts, or
          fingerprinting in the current implementation.
        </p>
      </LegalSection>

      <LegalSection
        id="account-information"
        title="Account and profile information"
      >
        <p>
          You create an account with a name, email address, and password. Your
          password is hashed with bcrypt before it is stored, and the plain
          password is never saved. The email address is used to identify your
          account, sign you in, and send password reset emails.
        </p>
        <p>
          {BRAND_NAME} currently does not offer &quot;Sign in with
          Google&quot; as an authentication method. Your {BRAND_NAME} account is
          separate from any Google account you choose to connect for Gmail.
        </p>
      </LegalSection>

      <LegalSection
        id="google-oauth"
        title="Google OAuth and Gmail data"
      >
        <p>
          Connecting Gmail is optional. It happens only when you choose
          &quot;Connect Gmail&quot; in the Connections area and approve the
          Google consent screen. Google OAuth is not used to sign in to{" "}
          {BRAND_NAME}.
        </p>
        <p className="font-medium text-foreground">
          What we request and access
        </p>
        <LegalList>
          <li>
            We request the Google scope{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
              https://www.googleapis.com/auth/gmail.readonly
            </code>
            . This is a read-only, restricted Gmail scope.
          </li>
          <li>
            We read messages from your Gmail inbox (the{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
              in:inbox
            </code>{" "}
            query). For each message we process the sender, subject, and body
            text. Attachments are not downloaded in the current implementation.
          </li>
          <li>
            We use your access token with Google&apos;s token information
            endpoint to display the connected Gmail address in the app.
          </li>
          <li>
            We request offline access so the application can refresh the
            connection and continue importing new inbox messages while you
            remain connected. The default polling interval is 30 seconds.
          </li>
        </LegalList>
        <p className="font-medium text-foreground">What we do not access</p>
        <LegalList>
          <li>
            We do not request Gmail send, modify, delete, or settings
            permissions.
          </li>
          <li>
            We do not request access to Google Drive, Google Calendar, Google
            Contacts, or any other Google service.
          </li>
          <li>
            We do not read the rest of your mailbox outside the inbox query
            described above.
          </li>
        </LegalList>
        <p className="font-medium text-foreground">
          How Google data is used, stored, and shared
        </p>
        <LegalList>
          <li>
            Gmail message data is used only to provide the features you see:
            the unified inbox, message prioritization, summaries, task
            extraction, search, analytics, and answers from the in-app
            assistant.
          </li>
          <li>
            Message text and limited metadata may be sent to our AI provider,
            Groq, for analysis (see the sharing section below).
          </li>
          <li>
            Google OAuth access and refresh tokens are encrypted with
            AES-256-CBC before they are written to MongoDB. The encryption key
            is stored in the backend environment, not in the browser.
          </li>
          <li>
            We do not sell Google user data, use it for advertising, or use it
            to build advertising profiles. We do not use Google user data to
            train our own AI models.
          </li>
        </LegalList>
        <p className="font-medium text-foreground">Disconnecting Gmail</p>
        <p>
          You can remove the Gmail connection at any time from the Connections
          page. The backend attempts to revoke the Google token, then deletes
          the stored access and refresh tokens. Messages that were already
          imported remain in your {BRAND_NAME} inbox until you delete them or
          request account deletion. You can also review or revoke this
          application&apos;s access directly in your{" "}
          <a
            href="https://myaccount.google.com/permissions"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Google Account permissions
          </a>
          .
        </p>
        <p>
          Our use of information received from Google APIs adheres to the{" "}
          <a
            href="https://developers.google.com/terms/api-services-user-data-policy"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Google API Services User Data Policy
          </a>
          , including the Limited Use requirements. Google&apos;s own handling
          of your data is described in the{" "}
          <a
            href="https://policies.google.com/privacy"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Google Privacy Policy
          </a>
          .
        </p>
      </LegalSection>

      <LegalSection id="how-we-use" title="How we use information">
        <LegalList>
          <li>Create and authenticate your account, and reset your password.</li>
          <li>
            Ingest and display your messages from manual entry, WhatsApp, and
            any Gmail account you connect.
          </li>
          <li>
            Run AI analysis to prioritize messages, produce summaries, recommend
            actions, and extract tasks and deadlines.
          </li>
          <li>Provide the dashboard, attention view, tasks, analytics, and assistant.</li>
          <li>Maintain security, prevent abuse, and diagnose errors.</li>
          <li>Respond to support and data requests sent to the contact address below.</li>
        </LegalList>
        <p>
          We do not use your information for advertising, profiling for ads, or
          sale to third parties.
        </p>
      </LegalSection>

      <LegalSection
        id="storage-and-protection"
        title="How information is stored and protected"
      >
        <p>
          Your account, messages, tasks, and connection records are stored in a
          MongoDB Atlas database. The application runs on hosting infrastructure
          (Vercel for the deployed frontend and backend). Data is transmitted
          over HTTPS in the production deployment.
        </p>
        <p>Security measures implemented in the codebase include:</p>
        <LegalList>
          <li>Passwords hashed with bcrypt; plain passwords are never stored.</li>
          <li>
            Google OAuth tokens encrypted with AES-256-CBC before storage, using
            a key held only in the backend environment.
          </li>
          <li>
            Password reset tokens stored only as SHA-256 hashes, with a
            30-minute expiry and single-use invalidation.
          </li>
          <li>
            Authentication cookies marked HttpOnly and, in production, Secure.
          </li>
          <li>
            Per-user scoping on database queries so one account cannot read or
            modify another account&apos;s data.
          </li>
          <li>
            API keys for AI and email providers kept on the backend and never
            exposed to the browser.
          </li>
        </LegalList>
        <p>
          No service can guarantee absolute security. If you believe your
          account or data has been compromised, contact us immediately.
        </p>
      </LegalSection>

      <LegalSection id="sharing" title="Data sharing and third-party services">
        <p>
          We do not sell your personal data. We share data only with service
          providers needed to run the application:
        </p>
        <LegalList>
          <li>
            <span className="text-foreground">Google</span> — OAuth consent and
            the Gmail API when you connect Gmail, plus token information used to
            display the connected address.
          </li>
          <li>
            <span className="text-foreground">Groq</span> — the AI provider
            currently used for message analysis and the assistant&apos;s general
            conversation replies. Message content and limited metadata (such as
            sender and prior thread context) may be sent to Groq for processing.
          </li>
          <li>
            <span className="text-foreground">Brevo</span> — transactional email
            delivery for password reset messages. Your email address and name may
            be included in that email.
          </li>
          <li>
            <span className="text-foreground">MongoDB Atlas</span> — database
            hosting and storage.
          </li>
          <li>
            <span className="text-foreground">Vercel</span> — application
            hosting and delivery.
          </li>
          <li>
            <span className="text-foreground">Meta / WhatsApp</span> — if
            WhatsApp ingestion is enabled, messages are delivered through
            Meta&apos;s WhatsApp Business Platform before they reach our webhook.
            Meta processes that data under its own terms and privacy policy.
          </li>
        </LegalList>
        <p>
          We may also disclose information if required by law or to protect the
          rights, safety, and security of the project, its users, or others. The
          project does not currently have a formal legal review process for such
          requests; this point should be reviewed before public launch.
        </p>
      </LegalSection>

      <LegalSection id="retention" title="Data retention">
        <LegalList>
          <li>
            Account data is retained while your account exists, until you
            request deletion.
          </li>
          <li>
            Messages and tasks are retained until you delete them in the app,
            clear your inbox, or request account deletion.
          </li>
          <li>
            Gmail connection tokens are retained until you disconnect Gmail or
            request deletion.
          </li>
          <li>
            Password reset tokens expire after 30 minutes and are removed after
            a successful reset.
          </li>
          <li>
            Authentication cookies expire after 7 days or when you sign out.
          </li>
          <li>
            Hosting and server logs are retained according to the hosting
            provider&apos;s configuration. The application does not set a custom
            log retention period.
          </li>
          <li>
            Database backups are managed by MongoDB Atlas according to the
            cluster plan. Backup retention has not been separately configured
            for this project.
          </li>
        </LegalList>
      </LegalSection>

      <LegalSection id="your-rights" title="Your rights and account/data deletion">
        <p>
          You can already do the following in the app:
        </p>
        <LegalList>
          <li>Sign out and end your session.</li>
          <li>Delete individual messages and clear your entire inbox.</li>
          <li>Disconnect Gmail, which revokes and deletes the stored tokens.</li>
          <li>Delete tasks extracted from your messages.</li>
        </LegalList>
        <p>
          To request access to, correction of, or deletion of your account and
          all associated data, email{" "}
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            {CONTACT_EMAIL}
          </a>
          . Account deletion is handled manually at present: there is no
          self-service &quot;delete account&quot; screen. We will verify your
          identity before acting on the request, then delete your user record,
          messages, tasks, and stored connection tokens, and revoke the Google
          token where possible.
        </p>
        <p>
          You may also withdraw consent for optional processing, such as the
          Gmail connection or AI analysis, by disconnecting the integration or
          asking us to delete your data. Depending on your jurisdiction, you may
          have additional rights; those rights and the applicable response
          periods need legal review.
        </p>
      </LegalSection>

      <LegalSection id="cookies" title="Cookies and authentication sessions">
        <p>
          {BRAND_NAME} uses a single authentication cookie named{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
            cai_token
          </code>{" "}
          to keep you signed in. It is HttpOnly, set for 7 days, and marked
          Secure when the deployment is configured for HTTPS. SameSite is Lax
          by default, or None with Secure when the frontend and backend are on
          different sites.
        </p>
        <p>
          The app also stores small interface preferences (such as your theme)
          in your browser&apos;s local storage. These stay on your device and are
          not sent to us as tracking data. A short-lived token may be used for
          the real-time WebSocket connection in development.
        </p>
        <p>
          We do not use advertising or cross-site tracking cookies. If analytics
          or other cookies are added later, this policy must be updated and, if
          required, consent must be requested.
        </p>
      </LegalSection>

      <LegalSection id="children" title="Children's privacy">
        <p>
          {BRAND_NAME} is not directed to children. We do not knowingly collect
          personal information from children below the minimum age permitted by
          applicable law (13 years old is the threshold used by many services;
          confirm the correct threshold for your jurisdiction). If you believe a
          child has provided us with personal information, contact us and we will
          delete it.
        </p>
      </LegalSection>

      <LegalSection id="changes" title="Changes to this policy">
        <p>
          We may update this policy as the project changes. The &quot;Last
          updated&quot; date at the top will change when we do. For material
          changes, we will try to notify users through the application or by
          email. Continuing to use {BRAND_NAME} after an update means you accept
          the revised policy.
        </p>
      </LegalSection>

      <LegalSection id="contact" title="Contact information">
        <p>
          For privacy questions, data requests, or security concerns, contact:
        </p>
        <p>
          <span className="text-foreground">Hamza Yaseen</span>
          <br />
          {BRAND_NAME} — Final Year Project, BBSUL
          <br />
          Email:{" "}
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            {CONTACT_EMAIL}
          </a>
        </p>
        <p>
          Please also review our{" "}
          <Link
            href="/terms"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Terms of Service
          </Link>
          .
        </p>
      </LegalSection>
    </LegalPageShell>
  );
}
