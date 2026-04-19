import React, { useState, useEffect, useMemo } from "react";
import {
    Tabs, Card, Text, Badge, ScrollArea, Container, Title,
    Flex, Button, TextInput, MultiSelect, Grid, Loader,
    Paper, Center, Divider, ActionIcon, Tooltip, Modal, Group, Stack
} from "@mantine/core";
import { debounce } from "lodash";
import { VariableSizeList as List } from "react-window";
import { fetchUsersByType, archiveUser, restoreUser } from "../../services/userService";
import { IconArchive, IconRestore, IconAlertCircle } from "@tabler/icons-react";
import { showNotification } from "@mantine/notifications";
import { showErrorNotification, showSuccessNotification } from "../../utils/errorHandler";

const InfoCard = React.memo(({ person, onArchive, onRestore }) => {
    const [loading, setLoading] = useState(false);
    const [confirmModal, setConfirmModal] = useState(false);
    const [actionType, setActionType] = useState(null);

    // Normalize gender display
    const normalizeGender = (gender) => {
        const genderMap = {
            'M': 'Male', 'male': 'Male', 'Male': 'Male',
            'F': 'Female', 'female': 'Female', 'Female': 'Female',
            'O': 'Other', 'other': 'Other', 'Other': 'Other'
        };
        return genderMap[gender] || gender || 'N/A';
    };

    const handleAction = async () => {
        setLoading(true);
        try {
            if (actionType === 'archive') {
                await onArchive(person.username);
                showSuccessNotification(`${person.full_name} has been archived`);
            } else {
                await onRestore(person.username);
                showSuccessNotification(`${person.full_name} has been restored`);
            }
        } catch (error) {
            showErrorNotification(error, 'Operation Failed');
        } finally {
            setLoading(false);
            setConfirmModal(false);
        }
    };

    const openConfirmModal = (action) => {
        setActionType(action);
        setConfirmModal(true);
    };

    return (
        <>
            <Card
                shadow="sm"
                radius="xl"
                withBorder
                p="lg"
                style={{
                    borderColor: "#e0e0e0",
                    backgroundColor: person.is_active ? "#fdfdfd" : "#fff5f5",
                    transition: "background-color 0.2s ease",
                }}
                className="info-card"
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f2f2f2")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = person.is_active ? "#fdfdfd" : "#fff5f5")}
            >
                <Flex justify="space-between" align="flex-start">
                    <div style={{ flex: 1 }}>
                        <Flex align="center" gap="xs">
                            <Text fw={600} size="lg">{person.full_name}</Text>
                            {!person.is_active && (
                                <Badge color="red" variant="filled" size="xs">Archived</Badge>
                            )}
                        </Flex>
                        <Text size="sm" c="dimmed"><strong>Username:</strong> {person.username}</Text>

                        {person.user_type === "student" && (
                            <>
                                <Divider my="sm" />
                                <Text size="sm"><strong>Programme:</strong> {person.programme}</Text>
                                <Text size="sm"><strong>Discipline:</strong> {person.discipline}</Text>
                                <Text size="sm"><strong>Batch:</strong> {person.batch}</Text>
                                <Text size="sm"><strong>Semester:</strong> {person.curr_semester_no}</Text>
                                <Text size="sm"><strong>Category:</strong> {person.category || 'N/A'}</Text>
                                <Text size="sm"><strong>Gender:</strong> {normalizeGender(person.gender)}</Text>
                            </>
                        )}

                        {person.user_type === "staff" && (
                            <>
                                <Divider my="sm" />
                                <Text size="sm"><strong>Gender:</strong> {normalizeGender(person.gender)}</Text>
                            </>
                        )}

                        {person.user_type === "faculty" && (
                            <>
                                <Divider my="sm" />
                                <Text size="sm"><strong>Department:</strong> {person.department}</Text>
                                <Text size="sm"><strong>Gender:</strong> {normalizeGender(person.gender)}</Text>
                                <Text size="sm" mb="xs"><strong>Designations:</strong></Text>
                                {person.designations.map((role, idx) => (
                                    <Badge key={idx} color="indigo" variant="light" radius="md" mr={5}>
                                        {role}
                                    </Badge>
                                ))}
                            </>
                        )}
                    </div>

                    <Flex direction="column" gap="xs">
                        {person.is_active ? (
                            <Tooltip label="Archive User">
                                <ActionIcon
                                    variant="light"
                                    color="orange"
                                    size="lg"
                                    onClick={() => openConfirmModal('archive')}
                                    disabled={loading}
                                >
                                    <IconArchive size={20} />
                                </ActionIcon>
                            </Tooltip>
                        ) : (
                            <Tooltip label="Restore User">
                                <ActionIcon
                                    variant="light"
                                    color="green"
                                    size="lg"
                                    onClick={() => openConfirmModal('restore')}
                                    disabled={loading}
                                >
                                    <IconRestore size={20} />
                                </ActionIcon>
                            </Tooltip>
                        )}
                    </Flex>
                </Flex>
            </Card>

            <Modal
                opened={confirmModal}
                onClose={() => setConfirmModal(false)}
                title={
                    <Text fw={600}>
                        {actionType === 'archive' ? 'Archive User' : 'Restore User'}
                    </Text>
                }
                centered
            >
                <Stack>
                    <Text>
                        {actionType === 'archive'
                            ? `Are you sure you want to archive ${person.full_name}? Their account will be deactivated.`
                            : `Are you sure you want to restore ${person.full_name}? Their account will be reactivated.`
                        }
                    </Text>
                    {actionType === 'archive' && (
                        <Text size="sm" c="orange">
                            <IconAlertCircle size={14} style={{ verticalAlign: 'middle' }} />
                            {' '}User must be inactive for at least 30 days before archival
                        </Text>
                    )}
                    <Group position="right" mt="md">
                        <Button
                            variant="default"
                            onClick={() => setConfirmModal(false)}
                            disabled={loading}
                        >
                            Cancel
                        </Button>
                        <Button
                            color={actionType === 'archive' ? 'orange' : 'green'}
                            onClick={handleAction}
                            loading={loading}
                        >
                            {actionType === 'archive' ? 'Archive' : 'Restore'}
                        </Button>
                    </Group>
                </Stack>
            </Modal>
        </>
    );
});

const extractUnique = (arr, key) => {
    // Special handling for gender to prevent duplicates and ensure proper mapping
    if (key === 'gender') {
        const genderMap = {
            'M': 'Male', 'male': 'Male', 'Male': 'Male',
            'F': 'Female', 'female': 'Female', 'Female': 'Female',
            'O': 'Other', 'other': 'Other', 'Other': 'Other'
        };

        const rawValues = arr.flatMap((item) => {
            const value = item[key];
            return value ? [String(value)] : [];
        }).filter(Boolean);

        // Map and deduplicate
        const mappedValues = rawValues.map(val => genderMap[val] || val);
        return [...new Set(mappedValues)].sort();
    }

    // Special handling for batch - show 2021+ first, then older batches
    if (key === 'batch') {
        const rawValues = arr.flatMap((item) => {
            const value = item[key];
            return value !== undefined && value !== null ? [String(value)] : [];
        }).filter(Boolean);

        // Separate batches into 2021+ and older
        const batches = [...new Set(rawValues)];
        const recentBatches = batches.filter(batch => {
            const batchYear = parseInt(batch);
            return !isNaN(batchYear) && batchYear >= 2021;
        });
        const olderBatches = batches.filter(batch => {
            const batchYear = parseInt(batch);
            return !isNaN(batchYear) && batchYear < 2021;
        });

        // Sort each group: recent ascending, older descending
        const sortedRecent = recentBatches.sort((a, b) => Number(a) - Number(b));
        const sortedOlder = olderBatches.sort((a, b) => Number(b) - Number(a));

        // Return recent batches first, then older ones
        return [...sortedRecent, ...sortedOlder];
    }

    // Special handling for semester to convert to string (kept for backward compatibility)
    if (key === "semester") {
        const rawValues = arr.flatMap((item) => {
            const value = item.curr_semester_no;
            return value !== undefined && value !== null ? [String(value)] : [];
        }).filter(Boolean);
        return [...new Set(rawValues)].sort((a, b) => Number(a) - Number(b));
    }

    // Special handling for designations (array field)
    if (key === "designations") {
        const rawValues = arr.flatMap((item) => item.designations || []);
        return [...new Set(rawValues)].sort();
    }

    // Default handling for other fields
    const rawValues = arr.flatMap((item) => {
        let value;
        // Handle discipline/department field mapping
        if (key === 'discipline') {
            value = item.discipline || item.department;
        } else {
            value = item[key];
        }
        return value !== undefined && value !== null && value !== '' ? [String(value)] : [];
    }).filter(Boolean);

    return [...new Set(rawValues)].sort();
};

const filterAndSearch = (data, filters, searchQuery) =>
    data.filter((person) => {
        const matchSearch = person.full_name.toLowerCase().includes(searchQuery.toLowerCase())
            || person.username.toLowerCase().includes(searchQuery.toLowerCase());

        const matchFilters = Object.entries(filters).every(([key, values]) => {
            if (values.length === 0) return true;
            if (key === "designations") return person.designations?.some((d) => values.includes(d));
            if (key === "discipline") {
                // Check both discipline and department fields for flexibility
                const disciplineValue = person.discipline || person.department;
                return values.includes(String(disciplineValue));
            }
            return values.includes(String(person[key]));
        });

        return matchSearch && matchFilters;
    });

const UserDirectory = () => {
    const [activeTab, setActiveTab] = useState("student");
    const [searchQuery, setSearchQuery] = useState("");
    const [filters, setFilters] = useState({
        programme: [], discipline: [], batch: [], category: [],
        department: [], designations: [], gender: []
    });
    const [data, setData] = useState({ student: [], faculty: [], staff: [] });
    const [loading, setLoading] = useState(false);
    const [filtering, setFiltering] = useState(false);

    const resetFilters = () => setFilters({
        programme: [], discipline: [], batch: [], category: [],
        department: [], designations: [], gender: []
    });

    const fetchData = async (tab = activeTab) => {
        setLoading(true);
        try {
            const res = await fetchUsersByType(tab);
            setData((prev) => ({ ...prev, [tab]: res || [] }));
        } catch (err) {
            showErrorNotification(err, 'Fetch Error');
        } finally {
            setLoading(false);
            resetFilters();
            setSearchQuery("");
        }
    };

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const handleArchive = async (username) => {
        await archiveUser(username);
        // Refresh the current tab data
        await fetchData(activeTab);
    };

    const handleRestore = async (username) => {
        await restoreUser(username);
        // Refresh the current tab data
        await fetchData(activeTab);
    };

    const currentData = data[activeTab] || [];

    const applicableFilters =
        activeTab === "student" ? ["programme", "discipline", "batch", "category", "gender"]
            : activeTab === "faculty" ? ["department", "designations", "gender"]
                : ["gender"];

    const handleSearchChange = useMemo(() =>
        debounce((value) => {
            setFiltering(true);
            setSearchQuery(value);
            setTimeout(() => setFiltering(false), 200);
        }, 200), []
    );

    const filteredData = useMemo(() =>
        filterAndSearch(currentData, filters, searchQuery),
        [currentData, filters, searchQuery]
    );

    // Simple filter data extraction - always show all available options
    const facultyDesignations = extractUnique(data.faculty, "designations");
    const availableProgrammes = extractUnique(currentData, 'programme');
    const availableDisciplines = extractUnique(currentData, 'discipline');

    const getItemSize = (index) => {
        const user = filteredData[index];
        if (user.user_type === "student") return 270;
        if (user.user_type === "faculty") return 250;
        return 150;
    };

    const VirtualList = () => (
        <List
            height={500}
            itemCount={filteredData.length}
            itemSize={getItemSize}
            width="100%"
            overscanCount={5}
        >
            {({ index, style }) => (
                <div style={{ ...style, padding: "0 8px", boxSizing: "border-box" }}>
                    <div style={{ marginBottom: 12 }}>
                        <InfoCard
                            person={filteredData[index]}
                            onArchive={handleArchive}
                            onRestore={handleRestore}
                        />
                    </div>
                </div>
            )}
        </List>
    );

    return (
        <Container size="lg" py="xl">
            <Flex
                direction={{ base: 'column', sm: 'row' }}
                gap={{ base: 'sm', sm: 'lg' }}
                justify={{ sm: 'center' }}
                mb="xl"
            >
                <Button
                    variant="gradient"
                    size="xl"
                    radius="xs"
                    gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                    sx={{ display: 'block', width: { base: '100%', sm: 'auto' }, whiteSpace: 'normal', padding: '1rem', textAlign: 'center' }}
                >
                    <Title order={1} sx={{ fontSize: { base: 'lg', sm: 'xl' }, lineHeight: 1.2, wordBreak: 'break-word' }}>
                        User Directory
                    </Title>
                </Button>
            </Flex>

            <Paper shadow="lg" p="xl" radius="xl" withBorder>
                <Tabs
                    value={activeTab}
                    onChange={setActiveTab}
                    variant="pills"
                    radius="lg"
                    color="blue"
                    keepMounted={false}
                >
                    <Tabs.List grow mb="lg">
                        <Tabs.Tab value="student">STUDENTS</Tabs.Tab>
                        <Tabs.Tab value="faculty">FACULTY</Tabs.Tab>
                        <Tabs.Tab value="staff">STAFF</Tabs.Tab>
                    </Tabs.List>

                    {["student", "faculty", "staff"].map((tabKey) => (
                        <Tabs.Panel value={tabKey} key={tabKey}>
                            <Grid mb="lg">
                                <Grid.Col span={12}>
                                    <TextInput
                                        size="md"
                                        radius="md"
                                        placeholder="🔍 Search by name or username"
                                        onChange={(e) => handleSearchChange(e.currentTarget.value)}
                                    />
                                </Grid.Col>

                                {applicableFilters.map((filterKey, idx) => (
                                    <Grid.Col span={6} key={idx}>
                                        <MultiSelect
                                            label={filterKey[0].toUpperCase() + filterKey.slice(1)}
                                            size="sm"
                                            placeholder={`Filter by ${filterKey}`}
                                            radius="md"
                                            value={filters[filterKey]}
                                            data={
                                                filterKey === "programme"
                                                    ? availableProgrammes
                                                    : filterKey === "discipline"
                                                        ? availableDisciplines
                                                        : filterKey === "designations"
                                                            ? facultyDesignations
                                                            : extractUnique(currentData, filterKey)
                                            }
                                            onChange={(value) => {
                                                // Simple independent filtering - no smart clearing
                                                setFilters((prev) => ({ ...prev, [filterKey]: value }));
                                            }}
                                            clearable
                                            searchable
                                        />
                                    </Grid.Col>
                                ))}
                            </Grid>

                            {loading || filtering ? (
                                <Center h={200}><Loader size="md" color="blue" /></Center>
                            ) : filteredData.length > 0 ? (
                                <ScrollArea h={500} offsetScrollbars>
                                    <VirtualList />
                                </ScrollArea>
                            ) : (
                                <Text align="center" c="dimmed">No users found.</Text>
                            )}
                        </Tabs.Panel>
                    ))}
                </Tabs>
            </Paper>
        </Container>
    );
};

export default UserDirectory;
