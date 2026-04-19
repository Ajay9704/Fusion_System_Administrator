import React, { useState, useEffect } from 'react';
import { Select, Group, Text, Badge, Tooltip, ActionIcon, Box } from '@mantine/core';
import { IconRefresh } from '@tabler/icons-react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { showErrorNotification, showSuccessNotification } from '../../utils/errorHandler';

const RoleSwitcher = () => {
    const { user } = useAuth();
    const [roles, setRoles] = useState([]);
    const [activeRole, setActiveRole] = useState(null);
    const [loading, setLoading] = useState(false);
    const [switching, setSwitching] = useState(false);

    const fetchAvailableRoles = async () => {
        setLoading(true);
        try {
            const response = await api.get('/roles/available/');
            setRoles(response.data.roles || []);

            // Set initial active role from localStorage
            const storedRoleId = localStorage.getItem('activeRoleId');
            if (storedRoleId) {
                const storedRole = response.data.roles.find(r => r.id === parseInt(storedRoleId));
                if (storedRole) {
                    setActiveRole(storedRole);
                }
            }

            // If no stored role, set first valid role as active
            if (!storedRoleId && response.data.roles.length > 0) {
                const firstValidRole = response.data.roles.find(r => r.is_valid);
                if (firstValidRole) {
                    setActiveRole(firstValidRole);
                    localStorage.setItem('activeRoleId', String(firstValidRole.id));
                }
            }
        } catch (error) {
            console.error('Failed to fetch roles:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchAvailableRoles();
        }
    }, [user]);

    const handleRoleSwitch = async (roleId) => {
        if (!roleId || roleId === activeRole?.id) return;

        setSwitching(true);
        try {
            const response = await api.post('/roles/switch/', {
                role_id: parseInt(roleId),
            });

            const newActiveRole = response.data.active_role;
            setActiveRole(newActiveRole);
            localStorage.setItem('activeRoleId', String(roleId));

            showSuccessNotification(`Now acting as ${newActiveRole.full_name}`, 'Role Switched');

            // Refresh the page to update permissions/UI
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } catch (error) {
            showErrorNotification(error, 'Role Switch Failed');
        } finally {
            setSwitching(false);
        }
    };

    if (loading || roles.length === 0) {
        return null;
    }

    // If user has only one role, don't show switcher
    if (roles.length === 1) {
        return (
            <Group spacing="xs">
                <Text size="sm" color="dimmed">Role:</Text>
                <Badge color="blue">{roles[0].name}</Badge>
            </Group>
        );
    }

    const roleOptions = roles
        .filter(role => role.is_valid)
        .map(role => ({
            value: String(role.id),
            label: role.full_name || role.name,
        }));

    return (
        <Group spacing="xs">
            <Text size="sm" color="dimmed">Active Role:</Text>
            <Box style={{ minWidth: 200 }}>
                <Select
                    size="xs"
                    placeholder="Select role"
                    data={roleOptions}
                    value={activeRole ? String(activeRole.id) : null}
                    onChange={handleRoleSwitch}
                    disabled={switching}
                    rightSection={
                        switching && (
                            <IconRefresh size={14} style={{ animation: 'spin 1s linear infinite' }} />
                        )
                    }
                    styles={{
                        root: { display: 'inline-block' },
                        input: {
                            minHeight: 30,
                            fontSize: 13,
                        },
                    }}
                />
            </Box>
            <Tooltip label="Refresh roles">
                <ActionIcon
                    size="sm"
                    variant="light"
                    onClick={fetchAvailableRoles}
                    loading={loading}
                >
                    <IconRefresh size={14} />
                </ActionIcon>
            </Tooltip>

            {/* Invalid roles warning */}
            {roles.some(r => !r.is_valid) && (
                <Tooltip label={`${roles.filter(r => !r.is_valid).length} role(s) unavailable due to temporal constraints`}>
                    <Badge color="orange" size="xs" variant="dot">
                        {roles.filter(r => r.is_valid).length}/{roles.length} Active
                    </Badge>
                </Tooltip>
            )}
        </Group>
    );
};

export default RoleSwitcher;
