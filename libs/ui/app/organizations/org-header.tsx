"use client";

import React from 'react';

interface Organization {
    id: number;
    name: string;
    slug: string;
    is_personal: boolean;
    // Other properties as needed
}

interface OrgHeaderProps {
    organization: Organization;
}

const OrgHeader = ({ organization }: OrgHeaderProps) => {
    if (!organization) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h1>{organization.name}</h1>
            <p>Organization ID: {organization.id}</p>
            <p>Slug: {organization.slug}</p>
            <p>Is Personal: {organization.is_personal ? 'Yes' : 'No'}</p>
            {/* Display other organization details as needed */}
        </div>
    );
};

export default OrgHeader;
