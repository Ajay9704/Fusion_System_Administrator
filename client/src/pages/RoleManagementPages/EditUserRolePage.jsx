import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Text,
  Stack,
  Modal,
  Flex,
  rem,
  TextInput,
  MultiSelect,
  Title,
  Badge,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import api from "../../services/api";
import { useMediaQuery } from "@mantine/hooks";
import { FaCheck, FaTimes } from 'react-icons/fa';
import { IconShield } from '@tabler/icons-react';

const EditUserRolePage = () => {
  const [username, setUsername] = useState("");
  const [userDetails, setUserDetails] = useState(null);
  const [roles, setRoles] = useState([]);
  const [currentRoles, setCurrentRoles] = useState([]);
  const [newRoles, setNewRoles] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const xIcon = <FaTimes style={{ width: rem(20), height: rem(20) }} />;
  const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

  const fetchUserAndRoleDetails = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/get-user-roles-by-username?username=${username}`
      );
      console.log('API Response:', response.data);
      setUserDetails(response.data.user);
      setCurrentRoles(response.data.roles || []);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      console.error('Error fetching user roles:', error.response?.data || error.message);
      notifications.show({
        title: "Error",
        icon: xIcon,
        position: "top-center",
        withCloseButton: true,
        message: error.response?.data?.message || "Could not fetch user details. Please check the username.",
        color: "red",
      });
    }
  };

  const handleSubmit = async () => {
    try {
      // Get all available role names
      const availableRoleNames = filterAvailableRoles().map(role => role.name);

      // Validate new roles before adding
      const invalidRoles = newRoles.filter(roleName => !availableRoleNames.includes(roleName));

      if (invalidRoles.length > 0) {
        notifications.show({
          title: "Invalid Roles",
          icon: xIcon,
          position: "top-center",
          withCloseButton: true,
          message: `The following roles cannot be assigned: ${invalidRoles.join(', ')}`,
          color: "orange",
        });
        return;
      }

      const updatedRoles = [...currentRoles, ...newRoles].filter(
        (role, index, self) => {
          // For role objects, check by name
          if (typeof role === 'object' && role.name) {
            return index === self.findIndex(r =>
              (typeof r === 'object' && r.name === role.name) || r === role.name
            );
          }
          // For string roles
          return index === self.findIndex(r =>
            (typeof r === 'object' && r.name === role) || r === role
          );
        }
      );

      console.log('Updated roles:', updatedRoles);

      await api.put(`/update-user-roles/`, {
        username: username,
        roles: updatedRoles,
      });

      notifications.show({
        title: "Success",
        position: "top-center",
        icon: checkIcon,
        withCloseButton: true,
        message: "User roles updated successfully.",
        color: "green",
      });
      setCurrentRoles(updatedRoles);
      fetchUserAndRoleDetails();
      setNewRoles([]);
      setIsOpen(false);
    } catch (error) {
      notifications.show({
        title: "Error",
        position: "top-center",
        icon: xIcon,
        withCloseButton: true,
        message: "Could not update user roles.",
        color: "red",
      });
    }
  };

  const handleRemoveRole = (role) => {
    setCurrentRoles((prevRoles) => prevRoles.filter((r) => r !== role));
  };

  const fetchAvailableRoles = async () => {
    try {
      const response = await api.get(`/view-roles`);
      setRoles(response.data);
    } catch (error) {
      console.log(error.response);
    }
  };

  const filterAvailableRoles = () => {
    if (!userDetails) return [];

    console.log('User details:', userDetails);
    console.log('All roles:', roles);

    // For now, show all non-basic roles
    // We'll add more specific filtering later
    const availableRoles = roles.filter(role => {
      // Skip base roles as they are already assigned
      return !role.basic;
    });

    console.log('Available roles after filtering:', availableRoles);
    return availableRoles;
  };

  useEffect(() => {
    fetchAvailableRoles();
  }, []);

  useEffect(() => {
    console.log('Current roles:', currentRoles);
    console.log('Available roles:', filterAvailableRoles());
  }, [userDetails, roles]);

  const handleEnterKeyPress = (event) => {
    if (event.key === "Enter") {
      fetchUserAndRoleDetails();
    }
  };

  useEffect(() => {
    document.addEventListener("keydown", handleEnterKeyPress);
    return () => {
      document.removeEventListener("keydown", handleEnterKeyPress);
    };
  }, [username, userDetails]);

  const matches = useMediaQuery('(min-width: 768px)');

  return (
    <Box
      style={{
        backgroundColor: "#f0f0f0",
        minHeight: "100vh",
        padding: "1rem",
      }}
    >
      {/* Title Button */}
      <Flex
        justify="center"
        align="center"
        style={{
          marginBottom: "2rem",
        }}
      >
        <Button
          variant="gradient"
          size="xl"
          radius="xs"
          gradient={{ from: "blue", to: "cyan", deg: 90 }}
          w={matches && "500px"}
          style={{
            fontSize: "1.8rem",
            lineHeight: 1.2,
          }}
        >
          <Title
            order={1}
            align="center"
            style={{
              fontSize: "1.25rem",
              wordBreak: "break-word",
            }}
          >
            {"Edit User's Role"}
          </Title>
        </Button>
      </Flex>

      <Flex
        direction={{ base: "column", lg: "row" }}
        style={{
          gap: "2rem",
          justifyContent: "center",
        }}
      >
        {/* First Section - Username Input */}
        <Box style={{ width: "100%", flex: 1 }}>
          <Stack spacing="1rem">
            <TextInput
              label="Username"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Button onClick={fetchUserAndRoleDetails}>Fetch User Details</Button>
          </Stack>

          {userDetails && (
            <Box
              style={{
                width: "100%",
                padding: "1rem",
                marginTop: "1rem",
                borderRadius: "8px",
                boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.1)",
                position: "relative",
                backgroundColor: "white",
              }}
            >
              {/* Status Label at the top right */}
              <Box
                style={{
                  position: "absolute",
                  top: "0.5rem",
                  right: "0.5rem",
                  backgroundColor: userDetails.is_active ? "green" : "red",
                  color: "white",
                  padding: "0.25rem 0.5rem",
                  borderRadius: "4px",
                }}
              >
                {userDetails.is_active ? "Active" : "Non-Active"}
              </Box>

              {/* User Details */}
              <Stack spacing="1rem">
                <Text style={{ fontSize: "1.1rem", fontWeight: "bold" }}>
                  Name: {userDetails.first_name}
                </Text>
                <Text style={{ fontSize: "1.1rem", fontWeight: "bold" }}>Roll No: {userDetails.username}</Text>

                {/* Display formatted date joined */}
                <Text style={{ fontSize: "1.1rem", fontWeight: "bold" }}>
                  Date Joined: {new Date(userDetails.date_joined).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </Text>
              </Stack>
            </Box>
          )}
        </Box>

        {/* Second Section - Current Roles and New Role Selection */}
        <Box
          style={{
            width: "100%",
            flex: 1,
            padding: "1rem",
            backgroundColor: "#fff",
            borderRadius: "8px",
            boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.1)",
            maxHeight: "400px",
          }}
        >
          {loading ? (
            <Text>Loading roles...</Text>
          ) : userDetails ? (
            <Box>
              <Text style={{ fontSize: "1.25rem", fontWeight: "bold" }}>Current Roles:</Text>
              {/* Scrollable roles section */}
              <Box
                style={{
                  maxHeight: "200px",
                  overflowY: "auto",
                  paddingRight: "1rem",
                }}
              >
                <Stack spacing="sm">
                  {currentRoles.map((role) => (
                    <Flex
                      key={role.id || role.name}
                      justify={"space-between"}
                      align={"center"}
                      style={{
                        padding: "0.75rem 1rem",
                        borderRadius: "6px",
                        fontWeight: "bold",
                        cursor: role.role_type === 'permanent' ? "pointer" : "default",
                        transition: "background-color 0.2s",
                        backgroundColor: role.role_type === 'temporary' ? '#fff5f5' : 'transparent',
                        border: role.role_type === 'temporary' ? '2px solid #ff922b' : '1px solid transparent',
                      }}
                      onMouseEnter={(e) => {
                        if (role.role_type === 'permanent') {
                          e.currentTarget.style.backgroundColor = "#f0f0f0";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (role.role_type === 'permanent') {
                          e.currentTarget.style.backgroundColor = "transparent";
                        }
                      }}
                    >
                      <Stack gap={4}>
                        <Flex gap="xs" align="center">
                          <Text>{role.name}{role.basic ? " (Base)" : ""}</Text>
                          {role.role_type === 'temporary' && (
                            <Badge 
                              color="orange" 
                              size="sm"
                              leftSection={<IconShield size={12} />}
                            >
                              {role.temporary_tag || 'EMERGENCY ACCESS'}
                            </Badge>
                          )}
                          {role.role_type === 'permanent' && !role.basic && (
                            <Badge 
                              color="green" 
                              size="sm"
                            >
                              {role.permanent_tag || 'PERMANENT'}
                            </Badge>
                          )}
                        </Flex>
                        {role.role_type === 'temporary' && role.time_remaining && (
                          <Text size="xs" style={{ color: '#ff922b', fontWeight: 600 }}>
                            ⏱️ Expires in: {role.time_remaining}
                          </Text>
                        )}
                        {role.role_type === 'temporary' && role.expires_at && (
                          <Text size="xs" c="dimmed">
                            Expiry: {new Date(role.expires_at).toLocaleString()}
                          </Text>
                        )}
                      </Stack>
                      {role.role_type === 'permanent' && (
                        <Button
                          variant="outline"
                          color="red"
                          disabled={role.basic}
                          onClick={() => handleRemoveRole(role)}
                          size="xs"
                        >
                          Remove
                        </Button>
                      )}
                      {role.role_type === 'temporary' && (
                        <Text size="xs" style={{ color: '#ff922b', fontWeight: 600 }}>
                          Auto-expiring
                        </Text>
                      )}
                    </Flex>
                  ))}
                </Stack>
              </Box>

              {/* Non-scrollable section */}
              <MultiSelect
                label="Add new role"
                placeholder="Select roles"
                data={filterAvailableRoles().map((role) => ({
                  value: role.name,
                  label: role.name,
                }))}
                value={newRoles}
                onChange={(values) => {
                  console.log('Selected roles:', values);
                  setNewRoles(values);
                }}
                searchable
                clearable
                disabled={!userDetails || filterAvailableRoles().length === 0}
                nothingFoundMessage="No roles available"
              />

              {filterAvailableRoles().length === 0 && (
                <Text size="sm" c="dimmed" mt="0.5rem">
                  No additional roles can be assigned to this user based on their designation and category.
                </Text>
              )}

              <Button
                color="blue"
                onClick={() => setIsOpen(true)}
                mt="1rem"
                fullWidth
              >
                Confirm Changes
              </Button>
            </Box>
          ) : (
            <Text>No user details found</Text>
          )}
        </Box>
      </Flex>

      {/* Confirmation Modal */}
      <Modal
        opened={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirm Changes"
      >
        <Text>Are you sure you want to update the user roles?</Text>
        <Flex justify="flex-end" gap="1rem" mt="1rem">
          <Button variant="default" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button color="blue" onClick={handleSubmit}>
            Confirm
          </Button>
        </Flex>
      </Modal>
    </Box>
  );
};

export default EditUserRolePage;