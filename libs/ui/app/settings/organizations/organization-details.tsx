"use client"

import React from 'react';
import { Organization } from "@/types/organization"
import { Member } from "@/types/member"

const OrganizationDetails = ({ organization, members }) => {
  return (
    <div>
      <h2>{organization.name}</h2>
      <div>
        <p>API Key: {organization.api_key}</p>
        <p>Slug: {organization.slug}</p>
      </div>
      <div>
        <h3>Members</h3>
        {/* Member management section */}
        {members.map(member => (
          <div key={member.id}>
            {member.first_name} {member.last_name}
            {/* Delete button here */}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrganizationDetails;

