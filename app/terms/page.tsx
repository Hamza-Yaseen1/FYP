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
  title: `Terms of Service — ${BRAND_NAME}`,
  description: `The terms that apply when you use ${BRAND_NAME}, an academic communication overload management project.`,
};

const reviewNotes = [
  "Confirm the operator/legal entity name and a contact address before public launch.",
  "Confirm the governing law and jurisdiction for these terms with a legal advisor.",
  "Confirm the intellectual-property and source-code licensing position for the project.",
  "Review whether the limitation-of-liability wording is enforceable in your jurisdiction.",
  "Confirm whether the app will remain available after the FYP assessment, and whether any service levels should be promised (the current app promises none).",
  "Check any university or institutional policies that apply to publishing this project publicly.",
];

export default function TermsOfServicePage() {
  return (
    <LegalPageShell
      title="Terms of Service"
      summary={`These terms govern your use of ${BRAND_NAME}. The project is an academic Final Year Project, and its features are provided for learning and demonstration purposes.`}
      reviewNotes={reviewNotes}
    >
      <LegalSection id="acceptance" title="1. Acceptance of terms">
        <p>
          By accessing or using {BRAND_NAME}, you agree to these Terms of
          Service. If you do not agree, do not use the application. If you use{" "}
          {BRAND_NAME} on behalf of an organisation, you confirm that you have
          authority to accept these terms for that organisation.
        </p>
        <p>
          These terms should be read together with our{" "}
          <Link
            href="/privacy"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Privacy Policy
          </Link>
          , which explains how we handle personal data.
        </p>
      </LegalSection>

      <LegalSection id="description" title={`2. About ${BRAND_NAME}`}>
        <p>
          {BRAND_NAME} is an Agentic AI System for Intelligent Communication
          Overload Management. It is a Final Year Project developed by Hamza
          Yaseen at BBSUL. It brings messages from different sources into one
          inbox, applies AI to prioritize them, summarizes content, extracts
          tasks and deadlines, and provides dashboards and an in-app assistant.
        </p>
        <p>
          {BRAND_NAME} is an academic project, not a commercial service. It is
          provided for learning, demonstration, and evaluation purposes. Features
          may change, be limited, or be withdrawn as the project develops.
        </p>
      </LegalSection>

      <LegalSection id="accounts" title="3. User accounts and responsibilities">
        <LegalList>
          <li>
            Provide accurate information when you create an account and keep it
            up to date.
          </li>
          <li>
            Keep your password confidential. You are responsible for activity
            that happens through your account.
          </li>
          <li>
            Do not share your account or use another person&apos;s account
            without permission.
          </li>
          <li>
            Tell us promptly at{" "}
            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="font-medium text-primary underline-offset-4 hover:underline"
            >
              {CONTACT_EMAIL}
            </a>{" "}
            if you believe your account has been compromised.
          </li>
          <li>
            You must meet the minimum age required by applicable law to use the
            service.
          </li>
          <li>
            If you connect a Gmail or WhatsApp account, you confirm that you are
            authorised to access that account and its messages.
          </li>
        </LegalList>
      </LegalSection>

      <LegalSection id="acceptable-use" title="4. Acceptable use">
        <p>You agree not to:</p>
        <LegalList>
          <li>
            Use {BRAND_NAME} for unlawful, harmful, fraudulent, or abusive
            activity.
          </li>
          <li>
            Access, collect, or process another person&apos;s messages without
            their permission.
          </li>
          <li>
            Attempt to gain unauthorised access to the application, other
            accounts, the database, or the hosting infrastructure.
          </li>
          <li>
            Probe, scan, overload, or interfere with the service, or bypass rate
            limits and security controls.
          </li>
          <li>
            Upload malware or content that infringes intellectual property,
            privacy, or other rights.
          </li>
          <li>
            Use the service in a way that violates Google&apos;s, Meta&apos;s, or
            WhatsApp&apos;s terms and policies.
          </li>
          <li>
            Resell, sublicense, or misrepresent the project as an official
            product of the university or any third party.
          </li>
        </LegalList>
        <p>
          We may suspend or remove access if we reasonably believe these rules
          have been broken, or if continuing access could harm the project, its
          users, or third parties.
        </p>
      </LegalSection>

      <LegalSection
        id="third-party-services"
        title="5. Third-party services"
      >
        <p>
          {BRAND_NAME} can connect to third-party services, currently Google
          Gmail (read-only) and WhatsApp message ingestion. Your use of those
          services is governed by their own terms and privacy policies. You can
          disconnect Gmail from the Connections page, and you can revoke access
          in your Google account settings.
        </p>
        <p>
          We are not responsible for the availability, accuracy, or practices of
          third-party services, or for any changes those providers make to their
          APIs.
        </p>
      </LegalSection>

      <LegalSection id="ai-limitations" title="6. AI-generated content limitations">
        <LegalList>
          <li>
            AI analysis is probabilistic. Priorities, summaries, recommended
            actions, extracted tasks, and deadlines can be incomplete,
            inaccurate, or out of date.
          </li>
          <li>
            AI output is a productivity aid, not professional advice. Do not rely
            on it as legal, medical, financial, or other professional advice.
          </li>
          <li>
            Always review important messages and AI-generated content yourself
            before acting on them or sending a reply.
          </li>
          <li>
            If the AI provider is unavailable or rate-limited, analysis may be
            marked as pending or fail. The application does not guarantee that
            every message is analyzed.
          </li>
          <li>
            The in-app assistant can make mistakes. Verify any answer that
            affects your decisions.
          </li>
        </LegalList>
      </LegalSection>

      <LegalSection id="availability" title="7. Service availability">
        <p>
          {BRAND_NAME} is provided on an &quot;as is&quot; and &quot;as
          available&quot; basis. As an academic project, it has no service-level
          agreement, uptime guarantee, or guaranteed support. The service may be
          unavailable during maintenance, university assessments, provider
          outages, quota limits, or Google OAuth verification changes.
        </p>
        <p>
          We may modify, suspend, or discontinue any part of the service at any
          time. You are responsible for keeping your own copy of any information
          you cannot afford to lose. The application does not currently provide
          a self-service data export tool.
        </p>
      </LegalSection>

      <LegalSection id="intellectual-property" title="8. Intellectual property">
        <p>
          You retain ownership of the content you submit or import, subject to
          the rights of the original senders and third-party providers. You grant
          us a limited permission to store, process, and transmit that content
          only as needed to provide the features you use, including sending
          message content to our AI provider for analysis.
        </p>
        <p>
          The {BRAND_NAME} name, interface design, and original source code are
          part of the academic project and belong to the project author, except
          for third-party open-source components used under their own licences.
          The licensing position for the source code should be confirmed before
          external reuse; do not assume it is open source.
        </p>
        <p>
          Google, Gmail, WhatsApp, and other product names are trademarks of
          their respective owners. {BRAND_NAME} is not endorsed by or affiliated
          with them.
        </p>
      </LegalSection>

      <LegalSection id="liability" title="9. Limitation of liability">
        <p>
          To the maximum extent permitted by applicable law, the project author
          is not liable for any indirect, incidental, special, consequential, or
          punitive damages, or for any loss of data, messages, tasks, profits,
          goodwill, or business opportunity arising from your use of{" "}
          {BRAND_NAME}.
        </p>
        <p>
          This includes losses caused by AI errors, missed or delayed messages,
          third-party service outages, provider rate limits, deletion of data, or
          unauthorised access where reasonable security measures were in place.
          Because this is a free academic project, you use it at your own risk.
          Some jurisdictions do not allow certain exclusions, so parts of this
          section may not apply to you. This section requires legal review before
          public launch.
        </p>
      </LegalSection>

      <LegalSection id="privacy" title="10. Privacy">
        <p>
          Our{" "}
          <Link
            href="/privacy"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Privacy Policy
          </Link>{" "}
          explains what data we collect, including Google Gmail data, and the
          choices available to you. It forms part of these terms.
        </p>
      </LegalSection>

      <LegalSection id="changes" title="11. Changes to these terms">
        <p>
          We may update these terms as the project changes. The &quot;Last
          updated&quot; date at the top will change when we do. For material
          changes, we will try to notify users through the application or by
          email. Continuing to use {BRAND_NAME} after an update means you accept
          the revised terms. If you do not agree, stop using the service.
        </p>
      </LegalSection>

      <LegalSection id="governing-law" title="12. Governing law">
        <p>
          These terms are intended to be governed by the laws of{" "}
          <span className="font-medium text-foreground">
            [jurisdiction to be confirmed — likely Pakistan, subject to legal
            review]
          </span>
          . Any disputes would be subject to the courts of that jurisdiction.
          This section must be confirmed before public launch.
        </p>
      </LegalSection>

      <LegalSection id="contact" title="13. Contact information">
        <p>
          For questions about these terms, contact:
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
      </LegalSection>
    </LegalPageShell>
  );
}
