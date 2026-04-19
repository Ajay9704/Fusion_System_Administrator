import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Box, Button, Text, Stack, Modal, Flex, TextInput,
  MultiSelect, Title, Badge, Group, Paper, Divider,
  Alert, Tooltip, ActionIcon,
} from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
import { IconAlertCircle, IconInfoCircle } from "@tabler/icons-react";
import apiClient from "../../services/api";
import { showErrorNotification, showSuccessNotification } from "../../utils/errorHandler";
import { ROLE_ELIGIBILITY, CONFLICTING_ROLES } from "../../utils/constants";

const EditUserRolePage = () => {
  const [username, setUsername] = useState("");
  const [userDetails, setUserDetails] = useState(null);
  const [allRoles, setAllRoles] = useState([]);
  const [currentRoles, setCurrentRoles] = useState([]);  // array of role objects
  const [newRoles, setNewRoles] = useState([]);           // array of role name strings to add
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const matches = useMediaQuery("(min-width: 768px)");

  // Load all available roles on mount
  useEffect(() => {
    apiClient.get("/view-roles/")
      .then(res => setAllRoles(res.data))
      .catch(err => showErrorNotification(err, "Roles Error"));
  }, []);

  const fetchUserAndRoleDetails = useCallback(async () => {
    if (!username.trim()) return;
    try {
      setLoading(true);
      const res = await apiClient.get(`/get-user-roles-by-username/?username=${username.trim()}`);

      if (!res.data.user) {
        throw new Error('User not found');
      }

      setUserDetails(res.data.user);
      setCurrentRoles(res.data.roles || []);   // [{id, name, full_name, ...}]
      setNewRoles([]);
    } catch (error) {
      if (error.response?.status === 404) {
        showErrorNotification(error, "User not found. Please check the username and try again.");
      } else {
        showErrorNotification(error, "Unable to fetch user details. Please try again.");
      }
      setUserDetails(null);
      setCurrentRoles([]);
    } finally {
      setLoading(false);
    }
  }, [username]);

  useEffect(() => {
    const handler = (e) => { if (e.key === "Enter") fetchUserAndRoleDetails(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [fetchUserAndRoleDetails]);

  const handleRemoveRole = (roleName) => {
    setCurrentRoles(prev => prev.filter(r => r.name !== roleName));
  };

  const handleSubmit = async () => {
    try {
      // Check for eligibility constraints
      if (userDetails) {
        const userType = userDetails.user_type; // 'faculty', 'staff', 'student'

        // Check if any selected roles are incompatible with user type
        const incompatibleRoles = [];
        const allSelectedRoles = [...currentRoles.map(r => r.name), ...newRoles];

        allSelectedRoles.forEach(roleName => {
          if (ROLE_ELIGIBILITY.faculty_only.includes(roleName) && userType !== 'faculty') {
            incompatibleRoles.push(`${roleName} (Faculty only)`);
          }
          if (ROLE_ELIGIBILITY.staff_only.includes(roleName) && userType !== 'staff') {
            incompatibleRoles.push(`${roleName} (Staff only)`);
          }
        });

        if (incompatibleRoles.length > 0) {
          alert(`Cannot assign the following roles to ${userType}:\n${incompatibleRoles.join('\n')}`);
          return;
        }

        // Check for conflicting roles
        const conflicts = [];
        allSelectedRoles.forEach(roleName => {
          if (CONFLICTING_ROLES[roleName]) {
            CONFLICTING_ROLES[roleName].forEach(conflictingRole => {
              if (allSelectedRoles.includes(conflictingRole)) {
                conflicts.push(`${roleName} conflicts with ${conflictingRole}`);
              }
            });
          }
        });

        if (conflicts.length > 0) {
          const confirmed = confirm(`Warning: The following role conflicts exist:\n${conflicts.join('\n')}\n\nDo you want to proceed anyway?`);
          if (!confirmed) return;
        }
      }

      // Merge current (possibly trimmed) roles + newly selected roles
      const currentNames = currentRoles.map(r => r.name);
      const merged = [...new Set([...currentNames, ...newRoles])];

      await apiClient.put("/update-user-roles/", {
        username: username.trim(),
        roles: merged,
      });

      showSuccessNotification("User roles updated successfully.");
      setIsOpen(false);
      setNewRoles([]);
      // Refresh
      await fetchUserAndRoleDetails();
    } catch (error) {
      if (error.response?.status === 403) {
        const errorMsg = error.response.data?.error || "You don't have permission to assign these roles.";
        showErrorNotification(error, "Role Assignment Denied: " + errorMsg);
      } else if (error.response?.status === 409) {
        const errorMsg = error.response.data?.error || "Role conflict detected.";
        showErrorNotification(error, "Role Conflict: " + errorMsg);
      } else {
        showErrorNotification(error, "Failed to update user roles. Please try again.");
      }
    }
  };

  // Check if a role is eligible for the current user
  const isRoleEligible = useCallback((roleName, userType) => {
    if (!userType) {
      // If no user type, show warning but allow all roles
      console.warn(`No user_type found for user. Allowing role '${roleName}' but this may need review.`);
      return true;
    }

    if (ROLE_ELIGIBILITY.faculty_only.includes(roleName)) {
      return userType === 'faculty';
    }
    if (ROLE_ELIGIBILITY.staff_only.includes(roleName)) {
      return userType === 'staff';
    }
    return true;
  }, []);

  // Check if role conflicts with any currently selected roles
  const getRoleConflicts = useCallback((roleName, currentRolesList) => {
    if (!CONFLICTING_ROLES[roleName]) return [];

    return currentRolesList.filter(r =>
      CONFLICTING_ROLES[roleName].includes(r)
    );
  }, []);

  // Filter addable roles based on eligibility
  const eligibleRoles = useMemo(() => {
    if (!userDetails) return addableRoles;

    const userType = userDetails.user_type;

    return addableRoles.filter(role => {
      const roleName = role.value;
      return isRoleEligible(roleName, userType);
    });
  }, [addableRoles, userDetails, isRoleEligible]);

  // Get role conflicts for display
  const roleConflicts = useMemo(() => {
    const allRolesList = [...currentRoles.map(r => r.name), ...newRoles];
    const conflicts = {};

    allRolesList.forEach(roleName => {
      const conflictsForRole = getRoleConflicts(roleName, allRolesList);
      if (conflictsForRole.length > 0) {
        conflicts[roleName] = conflictsForRole;
      }
    });

    return conflicts;
  }, [currentRoles, newRoles, getRoleConflicts]);

  // Roles available to add — exclude ones already assigned and check eligibility
  const currentRoleNames = new Set(currentRoles.map(r => r.name));
  const addableRoles = allRoles
    .filter(r => !currentRoleNames.has(r.name))
    .map(r => ({ value: r.name, label: `${r.name}${r.basic ? " (Base)" : ""}` }));

  return (
    <Box style={{ backgroundColor: "#f0f0f0", minHeight: "100vh", padding: "1rem" }}>
      <Flex justify="center" mb="2rem">
        <Button
          variant="gradient"
          size="xl"
          radius="xs"
          gradient={{ from: "blue", to: "cyan", deg: 90 }}
          w={matches ? "500px" : "100%"}
          style={{ fontSize: "1.8rem", lineHeight: 1.2 }}
        >
          <Title order={1} align="center" style={{ fontSize: "1.25rem", wordBreak: "break-word" }}>
            Edit User's Role
          </Title>
        </Button>
      </Flex>

      <Flex direction={{ base: "column", lg: "row" }} gap="2rem" justify="center">
        {/* Left — username lookup */}
        <Box style={{ flex: 1 }}>
          <Stack spacing="sm">
            <TextInput
              label="Username"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Button onClick={fetchUserAndRoleDetails} loading={loading}>
              Fetch User Details
            </Button>
          </Stack>

          {userDetails && (
            <Paper shadow="sm" p="md" mt="md" radius="md">
              <Badge
                color={userDetails.is_active ? "green" : "red"}
                variant="filled"
                mb="sm"
              >
                {userDetails.is_active ? "Active" : "Inactive"}
              </Badge>
              <Text fw={600}>Name: {userDetails.first_name} {userDetails.last_name}</Text>
              <Text>Username: {userDetails.username}</Text>
              <Text>User Type: {userDetails.user_type ? userDetails.user_type.toUpperCase() : 'Not Set'}</Text>
              <Text>Joined: {new Date(userDetails.date_joined).toLocaleDateString()}</Text>
              {!userDetails.user_type && (
                <Alert color="yellow" size="sm" mt="xs">
                  <Group>
                    <IconInfoCircle size={16} />
                    <Text size="sm">
                      User type is not set. Role eligibility checks may not work correctly.
                    </Text>
                  </Group>
                </Alert>
              )}
            </Paper>
          )}
        </Box>

        {/* Right — roles panel */}
        <Box style={{ flex: 1 }}>
          <Paper shadow="sm" p="md" radius="md">
            {!userDetails ? (
              <Text c="dimmed">Search for a user to manage their roles.</Text>
            ) : (
              <>
                <Text fw={600} size="lg" mb="sm">Current Roles</Text>
                <Divider mb="sm" />

                {currentRoles.length === 0 ? (
                  <Text c="dimmed" size="sm">No roles assigned.</Text>
                ) : (
                  <Stack spacing="xs" mb="md" style={{ maxHeight: 220, overflowY: "auto" }}>
                    {currentRoles.map((role) => (
                      <Flex key={role.id ?? role.name} justify="space-between" align="center"
                        style={{ padding: "6px 10px", borderRadius: 6, background: "#f8f8f8" }}>
                        <div>
                          <Text size="sm" fw={500}>{role.name}</Text>
                          {role.basic && <Badge size="xs" color="blue" variant="light">Base</Badge>}
                        </div>
                        <Button
                          size="xs"
                          variant="outline"
                          color="red"
                          disabled={role.basic}
                          onClick={() => handleRemoveRole(role.name)}
                        >
                          Remove
                        </Button>
                      </Flex>
                    ))}
                  </Stack>
                )}

                <MultiSelect
                  label="Add roles"
                  placeholder="Search and select roles to add"
                  data={eligibleRoles}
                  value={newRoles}
                  onChange={setNewRoles}
                  searchable
                  clearable
                  mb="md"
                  disabled={!userDetails}
                  description={
                    userDetails ?
                      `Showing ${eligibleRoles.length} eligible roles for ${userDetails.user_type}` :
                      "Select a user to see available roles"
                  }
                />

                {/* Show eligibility warnings */}
                {userDetails && eligibleRoles.length < addableRoles.length && (
                  <Alert color="yellow" size="sm" mb="md">
                    <Group>
                      <IconInfoCircle size={16} />
                      <Text size="sm">
                        Some roles are hidden because they are not eligible for <strong>{userDetails.user_type}</strong>.
                      </Text>
                    </Group>
                  </Alert>
                )}

                {/* Show conflict warnings */}
                {Object.keys(roleConflicts).length > 0 && (
                  <Alert color="orange" size="sm" mb="md">
                    <Group>
                      <IconAlertCircle size={16} />
                      <div>
                        <Text size="sm" fw={500}>Role conflicts detected:</Text>
                        {Object.entries(roleConflicts).map(([role, conflicts]) => (
                          <Text key={role} size="sm">
                            • <strong>{role}</strong> conflicts with: {conflicts.join(', ')}
                          </Text>
                        ))}
                      </div>
                    </Group>
                  </Alert>
                )}

                <Button fullWidth onClick={() => setIsOpen(true)}>
                  Confirm Changes
                </Button>
              </>
            )}
          </Paper>
        </Box>
      </Flex>

      <Modal opened={isOpen} onClose={() => setIsOpen(false)} title="Confirm Role Changes" centered>
        <Text mb="md">
          Update roles for <strong>{username}</strong>?
          {newRoles.length > 0 && <> Adding: <strong>{newRoles.join(", ")}</strong>.</>}
        </Text>
        <Group position="right">
          <Button variant="default" onClick={() => setIsOpen(false)}>Cancel</Button>
          <Button color="blue" onClick={handleSubmit}>Confirm</Button>
        </Group>
      </Modal>
    </Box>
  );
};

export default EditUserRolePage;
