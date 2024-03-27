import Sidebar from "@/components/sidebar"

import BillingModal from "./billing-modal"

interface RootLayoutProps {
  children: React.ReactNode
  profile: any
}

export default function RootLayout({ children, profile }: RootLayoutProps) {
  return (
    <section className="flex h-screen">
      {profile && process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY && (
        <BillingModal profile={profile} />
      )}
      <Sidebar />
      <div className="flex-1 overflow-auto">{children}</div>
    </section>
  )
}
