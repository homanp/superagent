export interface Organization {
    id: string
    slug: string
    name: string
    api_key: string
    stripe_customer_id?: string
    is_onboarded: string
    is_personal: boolean
    created_at: any
  }