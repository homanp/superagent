"use client"

import React, { useState, useEffect } from 'react';
import OrganizationList from './organization-list';
import OrganizationDetails from './organization-details';
import { Member } from "@/types/member"
import { Organization } from "@/types/organization"
import { Button } from "@/components/ui/button"
import CreateOrganization from './create-organization';
import AddMemberToOrganization from './add-member';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import { Profile } from '@/types/profile';

interface OrganizationsSettingsClientPageProps {
    profile: Profile
    user: any
    organizations: any
  }


const OrganizationSettingsClientPage: React.FC<OrganizationsSettingsClientPageProps> = ({
    profile,
    user,
    organizations,
}) => {
  const [selectedOrg, setSelectedOrg] = useState(null);
  const supabase = createClientComponentClient();
  const [members, setMembers] = useState([]);

    useEffect(() => {
        if (selectedOrg) {
            console.log("Selected Organization ID:", selectedOrg);
            fetch(`/organizations/listMembers?orgId=${selectedOrg.id}&userId=${user.id}`)
            .then(response => response.json())
            .then(data => setMembers(data))
            .catch(error => console.error('Error fetching members:', error));
        }
    }, [selectedOrg, user.id]);

  const handleOrgSelect = (org) => {
    setSelectedOrg(org);
    // Perform actions with the selected organization ID
  };
  return (
    <div className="grid grid-cols-4 gap-8 w-full">
      {/* Organization List */}
      <div className="col-span-1">
        <div className="flex flex-col space-y-2">
          <p className="text-sm font-bold">Organization List</p>
          <p className="text-muted-foreground text-sm">
            Select an organization from the list
          </p>
        </div>
        <div className="relative p-4">
          <OrganizationList
            organizations={organizations}
            onOrgSelect={handleOrgSelect}
          />
        </div>
        <CreateOrganization user={user} profile={profile} />
      </div>
      {/* Selected Organization Details */}
      {selectedOrg && (
        <div className="col-span-3">
          <div className="flex flex-col space-y-2">
            <p className="text-sm font-bold">Organization Details</p>
            <p className="text-muted-foreground text-sm">
              Details about the selected organization
            </p>
          </div>
          <div className="relative p-4">
            <OrganizationDetails organization={selectedOrg} members={members} />
          </div>
          <AddMemberToOrganization organization={selectedOrg} />
        </div>
      )}
    </div>
  );
  
};

export default OrganizationSettingsClientPage;
