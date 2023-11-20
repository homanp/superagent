import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  
  // Cookie handling for session management
  const cookieStore = cookies();
  const supabase = createRouteHandlerClient({ cookies: () => cookieStore });

  // Fetch current user and their profile
  const { data: { user }, error: userError } = await supabase.auth.getUser();
  if (userError || !user) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401 });
  }

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("*")
    .eq("user_id", user?.id)
    .single();

    if (profileError || !profile) {
      return new Response(JSON.stringify({ error: "Profile not found" }), { status: 403 });
    }

  // Verify if the user is part of the organization
  const { data: access, error: accessError } = await supabase
    .from('profile_organization')
    .select('*')
    .eq('profile_id', profile?.id)
    .eq('organization_id', orgId)

  if (accessError || !access) {
    return new Response(JSON.stringify({ error: "Access denied" }), { status: 403 });
  }

  // First, fetch the list of profile IDs associated with the organization
  const { data: profileIds, error: profileIdsError } = await supabase
    .from('profile_organization')
    .select('profile_id')
    .eq('organization_id', orgId);

  if (profileIdsError) {
    console.error(profileIdsError);
    return; // or handle the error as needed
  }

  // Extract the profile IDs from the results
  const ids = profileIds.map(p => p.profile_id);

  // Then, fetch the profiles using the list of IDs
  const { data: members, error: membersError } = await supabase
    .from('profiles')
    .select('firt_name, last_name, company, id')
    .in('id', ids)
    .select();

    if (membersError) {
      return new Response(JSON.stringify({ error: membersError.message }), { status: 500 });
    }
    console.log('members', members);
    return new Response(JSON.stringify(members));
}