import { cookies } from "next/headers"
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs"
import Stripe from "stripe"

import { Api } from "@/lib/api"
import { stripe } from "@/lib/stripe"

import WorkflowCards from "./cards"
import CheckoutSessionStatus from "./checkout-session-status"
import Header from "./header"

export const dynamic = "force-dynamic"

export default async function Workflows({
  searchParams,
}: {
  searchParams: { checkout_session_id: string }
}) {
  const supabase = createRouteHandlerClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  const { data: profile } = await supabase
    .from("profiles")
    .select("*")
    .eq("user_id", user?.id)
    .single()
  const api = new Api(profile.api_key)

  const { data: workflows } = await api.getWorkflows()

  let checkoutSession: Stripe.Checkout.Session | undefined
  if (searchParams.checkout_session_id) {
    try {
      checkoutSession = await stripe.checkout.sessions.retrieve(
        searchParams.checkout_session_id
      )
    } catch (error) {}
  }

  return (
    <div className="flex h-screen w-full flex-col justify-between space-y-4 overflow-hidden">
      {checkoutSession && (
        <CheckoutSessionStatus
          // passing json object to the client component
          session={JSON.parse(JSON.stringify(checkoutSession))}
        />
      )}
      <Header profile={profile} />
      <WorkflowCards workflows={workflows} />
    </div>
  )
}
