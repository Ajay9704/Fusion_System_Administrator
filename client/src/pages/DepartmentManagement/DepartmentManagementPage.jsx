import React, { useState, useEffect } from 'react';
import {
    Container, Title, Paper, Stack, Group, Button, Text, TextInput,
    Modal, Select, ActionIcon, Tooltip, Badge, ScrollArea, Divider,
    Box, Collapse, Chip
} from '@mantine/core';
import {
    IconPlus, IconEdit, IconTrash, IconChevronDown, IconChevronRight,
    IconBuilding, IconHierarchy, IconUsers, IconSearch, IconX
} from '@tabler/icons-react';
import api from '../../services/api';
import { showErrorNotification, showSuccessNotification } from '../../utils/errorHandler';

const DepartmentManagementPage = () => {
    const [departments, setDepartments] = useState([]);
    const [tree, setTree] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [editingDept, setEditingDept] = useState(null);
    const [formData, setFormData] = useState({ name: '', parent_id: '' });
    const [expandedNodes, setExpandedNodes] = useState({});
    const [searchQuery, setSearchQuery] = useState('');
    const [highlightedDeptId, setHighlightedDeptId] = useState(null);


    const fetchDepartments = async () => {
        setLoading(true);
        try {
            // Get flat list of departments for the select dropdown
            const response = await api.get('/departments/');

            // Ensure it's an array
            const departmentsArray = Array.isArray(response.data) ? response.data : [];
            setDepartments(departmentsArray);
        } catch (error) {
            showErrorNotification(error, 'Fetch Error');
            setDepartments([]); // Set to empty array on error
        } finally {
            setLoading(false);
        }
    };

    const fetchTree = async () => {
        try {
            const response = await api.get('/departments/tree/');
            setTree(response.data.tree || []);
        } catch (error) {
        }
    };

    useEffect(() => {
        fetchDepartments();
        fetchTree();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            if (editingDept) {
                // Update existing department
                await api.put(`/departments/${editingDept.id}/update/`, {
                    name: formData.name,
                    parent_id: formData.parent_id || null,
                });
                showSuccessNotification('Department updated successfully');
            } else {
                // Create new department
                await api.post('/departments/create/', {
                    name: formData.name,
                    parent_id: formData.parent_id || null,
                });
                showSuccessNotification('Department created successfully');
            }

            setModalOpen(false);
            setEditingDept(null);
            setFormData({ name: '', parent_id: '' });
            fetchDepartments();
            fetchTree();
        } catch (error) {
            showErrorNotification(error, 'Operation Failed');
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (dept) => {
        setEditingDept(dept);
        setFormData({
            name: dept.name,
            parent_id: dept.parent_id ? String(dept.parent_id) : '',
        });
        setModalOpen(true);
    };

    const handleDelete = async (dept) => {
        if (!confirm(`Are you sure you want to delete "${dept.name}"?`)) {
            return;
        }

        setLoading(true);
        try {
            await api.delete(`/departments/${dept.id}/delete/`);
            showSuccessNotification('Department deleted successfully');
            fetchDepartments();
            fetchTree();
        } catch (error) {
            showErrorNotification(error, 'Delete Failed');
        } finally {
            setLoading(false);
        }
    };

    const openCreateModal = () => {
        setEditingDept(null);
        setFormData({ name: '', parent_id: '' });
        setModalOpen(true);
    };

    const toggleNode = (nodeId) => {
        setExpandedNodes(prev => {
            const currentState = prev[nodeId] === undefined ? true : prev[nodeId];
            const newState = !currentState;
            return {
                ...prev,
                [nodeId]: newState
            };
        });
    };

    const expandAllNodes = () => {
        // Set all nodes to explicitly expanded (true)
        const allExpanded = {};
        const collectNodeIds = (nodes) => {
            nodes.forEach(node => {
                allExpanded[node.id] = true;
                if (node.children && node.children.length > 0) {
                    collectNodeIds(node.children);
                }
            });
        };
        collectNodeIds(tree);
        setExpandedNodes(allExpanded);
    };

    const collapseAllNodes = () => {
        // Set all nodes to explicitly collapsed (false)
        const allCollapsed = {};
        const collectNodeIds = (nodes) => {
            nodes.forEach(node => {
                allCollapsed[node.id] = false;
                if (node.children && node.children.length > 0) {
                    collectNodeIds(node.children);
                }
            });
        };
        collectNodeIds(tree);
        setExpandedNodes(allCollapsed);
    };

    const searchDepartments = () => {
        if (!searchQuery.trim()) {
            setHighlightedDeptId(null);
            return;
        }

        // Find all matching departments
        const findMatchingNodes = (nodes) => {
            const matches = [];
            for (const node of nodes) {
                if (node.name.toLowerCase().includes(searchQuery.toLowerCase())) {
                    matches.push(node.id);
                }
                if (node.children && node.children.length > 0) {
                    matches.push(...findMatchingNodes(node.children));
                }
            }
            return matches;
        };

        const matchingIds = findMatchingNodes(tree);
        
        if (matchingIds.length > 0) {
            setHighlightedDeptId(matchingIds[0]);

            // Expand all nodes to show all matches
            const newExpanded = {};
            const expandAll = (nodes) => {
                nodes.forEach(node => {
                    newExpanded[node.id] = true;
                    if (node.children && node.children.length > 0) {
                        expandAll(node.children);
                    }
                });
            };
            expandAll(tree);
            setExpandedNodes(newExpanded);
            
            showSuccessNotification(`Found ${matchingIds.length} matching department(s)`);
        } else {
            setHighlightedDeptId(null);
            showErrorNotification(new Error('No matching department found'), 'Search Result');
        }
    };

    const clearSearch = () => {
        setSearchQuery('');
        setHighlightedDeptId(null);
    };

    // Filter tree based on search query
    const filteredTree = searchQuery.trim() ? tree : tree;

    const TreeNode = ({ node, level = 0 }) => {
        // If expandedNodes[node.id] is undefined, default to true (expanded) for root nodes, false for others
        const isExpanded = expandedNodes[node.id] === undefined ? (level === 0) : expandedNodes[node.id];
        const hasChildren = node.children && node.children.length > 0;
        const isHighlighted = highlightedDeptId === node.id;

        // Visual indicators based on level
        const levelColors = ['#1971c2', '#2f9e44', '#e8590c', '#9c36b5', '#e03131'];
        const levelColor = levelColors[level % levelColors.length];

        return (
            <Box>
                <Group
                    spacing="xs"
                    p="xs"
                    sx={{
                        borderLeft: `3px solid ${levelColor}`,
                        marginLeft: `${level * 24}px`,
                        paddingLeft: '12px',
                        backgroundColor: isHighlighted ? '#fff3cd' : (level === 0 ? '#f8f9fa' : 'transparent'),
                        '&:hover': { backgroundColor: '#e9ecef' },
                        borderRadius: '4px',
                        marginBottom: '4px',
                        border: isHighlighted ? '2px solid #ffc107' : 'none',
                    }}
                >
                    {hasChildren ? (
                        <ActionIcon
                            size="md"
                            variant="filled"
                            onClick={() => toggleNode(node.id)}
                            color={levelColor}
                            style={{ cursor: 'pointer' }}
                        >
                            {isExpanded ? <IconChevronDown size={18} /> : <IconChevronRight size={18} />}
                        </ActionIcon>
                    ) : (
                        <Box style={{ width: 36 }} />
                    )}

                    <Box style={{ flex: 1 }}>
                        <Group spacing="xs" position="apart">
                            <Group spacing="xs">
                                <IconBuilding size={16} color={levelColor} />
                                <Text size="sm" weight={600}>
                                    {node.name}
                                </Text>
                                {level === 0 && (
                                    <Badge size="xs" color="blue" variant="light">
                                        Root
                                    </Badge>
                                )}
                                {level > 0 && (
                                    <Badge size="xs" color={levelColor} variant="light">
                                        Level {level}
                                    </Badge>
                                )}
                            </Group>

                            <Group spacing={4}>
                                {hasChildren && (
                                    <Badge size="xs" color="gray" variant="outline">
                                        {node.children.length} {node.children.length === 1 ? 'child' : 'children'}
                                    </Badge>
                                )}
                                <Tooltip label="Edit">
                                    <ActionIcon
                                        size="sm"
                                        color="blue"
                                        variant="light"
                                        onClick={() => {
                                            const dept = departments.find(d => d.id === node.id);
                                            if (dept) handleEdit(dept);
                                        }}
                                    >
                                        <IconEdit size={14} />
                                    </ActionIcon>
                                </Tooltip>
                                <Tooltip label="Delete">
                                    <ActionIcon
                                        size="sm"
                                        color="red"
                                        variant="light"
                                        onClick={() => {
                                            const dept = departments.find(d => d.id === node.id);
                                            if (dept) handleDelete(dept);
                                        }}
                                    >
                                        <IconTrash size={14} />
                                    </ActionIcon>
                                </Tooltip>
                            </Group>
                        </Group>
                    </Box>
                </Group>

                {hasChildren && isExpanded && (
                    <Collapse in={isExpanded}>
                        {node.children.map(child => (
                            <TreeNode key={child.id} node={child} level={level + 1} />
                        ))}
                    </Collapse>
                )}
            </Box>
        );
    };

    const parentOptions = departments
        .filter(dept => !editingDept || dept.id !== editingDept.id)
        .map(dept => ({
            value: String(dept.id),
            label: `${'  '.repeat(dept.level)}${dept.name}`,
        }));

    return (
        <Container size="lg" py="xl">
            <Stack>
                <Group position="apart" align="center">
                    <Title order={2}>Department Management</Title>
                    <Button
                        onClick={openCreateModal}
                    >
                        <IconPlus size={16} style={{ marginRight: '8px' }} />
                        Add Department
                    </Button>
                </Group>

                <Paper shadow="sm" p="md" withBorder>
                    <Stack>
                        <Group position="apart">
                            <Group spacing="xs">
                                <IconHierarchy size={20} />
                                <Text weight={600} size="lg">Department Hierarchy</Text>
                            </Group>
                            <Group spacing="xs">
                                <Chip size="xs" checked={false}>
                                    {departments.length} total
                                </Chip>
                                <Chip size="xs" checked={false} color="blue">
                                    {tree.length} root
                                </Chip>
                                <TextInput
                                    placeholder="Search departments..."
                                    size="xs"
                                    style={{ width: '200px' }}
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.currentTarget.value)}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                            searchDepartments();
                                        }
                                    }}
                                    rightSection={
                                        searchQuery ? (
                                            <ActionIcon size="sm" onClick={clearSearch}>
                                                <IconX size={14} />
                                            </ActionIcon>
                                        ) : (
                                            <ActionIcon size="sm" onClick={searchDepartments}>
                                                <IconSearch size={14} />
                                            </ActionIcon>
                                        )
                                    }
                                />
                                <Button
                                    size="xs"
                                    variant="filled"
                                    color="green"
                                    onClick={() => {
                                        expandAllNodes();
                                    }}
                                    style={{ cursor: 'pointer' }}
                                >
                                    Expand All
                                </Button>
                                <Button
                                    size="xs"
                                    variant="filled"
                                    color="red"
                                    onClick={() => {
                                        collapseAllNodes();
                                    }}
                                    style={{ cursor: 'pointer' }}
                                >
                                    Collapse All
                                </Button>
                            </Group>
                        </Group>

                        <Divider />

                        {tree.length === 0 ? (
                            <Box p="xl" sx={{ textAlign: 'center' }}>
                                <IconHierarchy size={48} color="#adb5bd" />
                                <Text color="dimmed" mt="sm">No departments created yet</Text>
                                <Button
                                    variant="light"
                                    mt="md"
                                    onClick={openCreateModal}
                                >
                                    <IconPlus size={16} style={{ marginRight: '8px' }} />
                                    Add First Department
                                </Button>
                            </Box>
                        ) : (
                            <ScrollArea.Autosize mah={500}>
                                <Box p="sm">
                                    {filteredTree.map(node => (
                                        <TreeNode key={node.id} node={node} />
                                    ))}
                                </Box>
                            </ScrollArea.Autosize>
                        )}
                    </Stack>
                </Paper>

                <Paper shadow="sm" p="md" withBorder>
                    <Group spacing="xs" mb="md">
                        <IconUsers size={20} />
                        <Title order={4}>All Departments</Title>
                    </Group>
                    <Stack spacing="xs">
                        {departments.map(dept => (
                            <Group key={dept.id} position="apart" p="sm" sx={{
                                backgroundColor: dept.level === 0 ? '#f8f9fa' : 'transparent',
                                borderLeft: `3px solid ${dept.level === 0 ? '#1971c2' : '#868e96'}`,
                                borderRadius: '4px',
                            }}>
                                <div style={{ flex: 1 }}>
                                    <Group spacing="xs">
                                        <IconBuilding size={16} />
                                        <Text size="sm" weight={600}>
                                            {dept.name}
                                        </Text>
                                        {dept.level === 0 && (
                                            <Badge size="xs" color="blue" variant="light">Root</Badge>
                                        )}
                                        {dept.parent_name && (
                                            <Badge size="xs" color="gray" variant="outline">
                                                Parent: {dept.parent_name}
                                            </Badge>
                                        )}
                                    </Group>
                                    <Text size="xs" color="dimmed" mt={4}>
                                        Level {dept.level} • ID: {dept.id}
                                    </Text>
                                </div>
                                <Group spacing="xs">
                                    {dept.has_children && (
                                        <Badge size="xs" color="green" variant="light">
                                            Has children
                                        </Badge>
                                    )}
                                    <Tooltip label="Edit">
                                        <ActionIcon
                                            size="sm"
                                            color="blue"
                                            variant="light"
                                            onClick={() => handleEdit(dept)}
                                        >
                                            <IconEdit size={14} />
                                        </ActionIcon>
                                    </Tooltip>
                                    <Tooltip label="Delete">
                                        <ActionIcon
                                            size="sm"
                                            color="red"
                                            variant="light"
                                            onClick={() => handleDelete(dept)}
                                        >
                                            <IconTrash size={14} />
                                        </ActionIcon>
                                    </Tooltip>
                                </Group>
                            </Group>
                        ))}
                    </Stack>
                </Paper>
            </Stack>

            <Modal
                opened={modalOpen}
                onClose={() => setModalOpen(false)}
                title={editingDept ? 'Edit Department' : 'Create Department'}
                centered
            >
                <form onSubmit={handleSubmit}>
                    <Stack>
                        <TextInput
                            label="Department Name"
                            placeholder="e.g., Computer Science"
                            required
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        />

                        <Select
                            label="Parent Department"
                            placeholder="Select parent department (optional)"
                            clearable
                            searchable
                            data={parentOptions}
                            value={formData.parent_id}
                            onChange={(value) => setFormData({ ...formData, parent_id: value || '' })}
                        />

                        <Group position="right" mt="md">
                            <Button
                                variant="default"
                                onClick={() => setModalOpen(false)}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                loading={loading}
                            >
                                {editingDept ? 'Update' : 'Create'}
                            </Button>
                        </Group>
                    </Stack>
                </form>
            </Modal>
        </Container>
    );
};

export default DepartmentManagementPage;
