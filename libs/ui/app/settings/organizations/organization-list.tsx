import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableRow, TableCell } from '@/components/ui/table';
import { Organization } from '@/types/organization';

const OrganizationList = ({ organizations, onOrgSelect }) => {
  if (!Array.isArray(organizations) || organizations.length === 0) {
    // Handle empty or invalid organizations data
    return <div>No organizations available</div>;
  }
  const [selectedOrgId, setSelectedOrgId] = useState(null);

  useEffect(() => {
    if (!selectedOrgId) {
      const personalOrg = organizations.find(org => org.is_personal);
      if (personalOrg) {
        setSelectedOrgId(personalOrg.id);
        onOrgSelect(personalOrg);
      }
    }
  }, [organizations, onOrgSelect, selectedOrgId]);

  const handleOrgClick = (org) => {
    setSelectedOrgId(org.id);
    onOrgSelect(org);
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableBody>
          {organizations.map((org) => (
            <TableRow
              key={org.id}
              data-state={selectedOrgId === org.id ? "selected" : ""}
              onClick={() => handleOrgClick(org)}
              >
              <TableCell className="py-3"
              >
                {org.name}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default OrganizationList;
