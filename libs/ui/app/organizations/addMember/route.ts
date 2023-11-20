import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { NextApiResponse } from 'next';
import { cookies } from 'next/headers';

interface RequestBody {
  profileId: string;
  organizationId: number;
}

export async function POST(request: Request) {
  const cookieStore = cookies();
  const supabase = createRouteHandlerClient({ cookies: () => cookieStore });

  // Authenticate the user
  const { data: {user}, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401 });
  }

  const { profileId, organizationId }: RequestBody = await request.json();

  // Verify organization exists
  const { data: organization, error: organizationError } = await supabase
    .from('organizations')
    .select('*')
    .eq('id', organizationId)
    .single();

  if (organizationError || !organization) {
    return new Response(JSON.stringify({ error: "Organization not found" }), { status: 404 });
  }

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("*")
    .eq("user_id", user?.id)
    .single();

  if (profileError || !profile) {
    return new Response(JSON.stringify({ error: "Profile not found" }), { status: 403 });
  }

  // Check if authenticated user has access to the organization
  const { data: access, error: accessError } = await supabase
    .from('profile_organization')
    .select('*')
    .eq('profile_id', profile.id)
    .eq('organization_id', organizationId);

  if (accessError || !access) {
      return new Response(JSON.stringify({ error: "Access denied" }), { status: 403 });
  }

    // // Check if the email corresponds to a user
    // const { data: supabaseUser, error: userError } = await supabase.auth.getUserByEmail(email);
    // if (userError || !supabaseUser) {
    //     return new Response(JSON.stringify({ error: "User not found" }), { status: 404 });
    // }

  // Find the profile associated with the user
  console.log('profileId', profileId);  
  const { data: userProfile, error: userProfileError } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', profileId)
    .single();

  if (userProfileError || !userProfile) {
    return new Response(JSON.stringify({ error: "Profile not found" }), { status: 404 });
  }




  // Add the user to the organization
  const { error: addUserError } = await supabase
    .from('profile_organization')
    .insert({ profile_id: userProfile.id, organization_id: organizationId });

  if (addUserError) {
    return new Response(JSON.stringify({ error: addUserError.message }), { status: 500 });
  }

  return new Response(JSON.stringify({ message: "User added successfully" }), { status: 200 });
}
