import React from 'react';
import OrganizationSettingsClientPage from './client-page';
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs"
import { cookies } from "next/headers"

export const dynamic = "force-dynamic"

export default async function OrganizationSettingsPage() {
  const supabase = createRouteHandlerClient({ cookies });
  
  // Fetch current user and their profile
  const { data: { user }, } = await supabase.auth.getUser()
  const { data: profile } = await supabase
    .from("profiles")
    .select("*")
    .eq("user_id", user?.id)
    .single();
  
  // Fetch organizations with profile details
  const { data: orgData, error: orgError } = await supabase
    .from('organizations')
    .select('*')
    .in('id', await supabase.from('profile_organization')
      .select('organization_id')
      .eq('profile_id', profile?.id)
      .then(res => res.data?.map(po => po.organization_id) || [])
    );

  if (orgError) throw orgError;
  
  // Return combined data
  return user ? <OrganizationSettingsClientPage profile={profile} user={user} organizations={orgData} />: null
}