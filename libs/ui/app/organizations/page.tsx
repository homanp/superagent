import { cookies } from "next/headers";
import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import OrgHeader from './org-header';
// import OrgMembers from './org-members'; // Assuming you have this component

export const dynamic = "force-dynamic";


export default async function OrganizationDashboard() {
  const supabase = createServerComponentClient({ cookies });
  const {
    data: { user },
  } = await supabase.auth.getUser()

    // If no user is found, return an unauthorized message
    if (!user) {
        return <div>Unauthorized access</div>;
      }

    // Fetch the profile ID for the logged-in user
    const profileResponse = await supabase
    .from('profiles')
    .select('id')
    .eq('user_id', user?.id)
    .single();

    

    if (profileResponse.error) {
    console.error('Error fetching profile:', profileResponse.error);
    return null; // or handle the error as needed
    }

    const profileId = profileResponse.data.id;

    // Now fetch the organization details using the profile ID
    const { data, error } = await supabase
    .from('profile_organization')
    .select(`
      organizations (
        id, name, slug, is_personal
      )
    `)
    .eq('profile_id', profileId)
    .eq('organizations.is_personal', true)
    .single();

    if (error) {
    console.error('Error fetching organization:', error);
    return null; // or handle the error as needed
    }

    // Ensure the organization object matches the Organization interface
    const organizationData = data?.organizations
  

  return (
    <div>
      <OrgHeader organization={data?.organizations} />
      {/* <OrgMembers organizationId={organizationId} /> */}
      {/* Other components as needed */}
    </div>
  );
}
