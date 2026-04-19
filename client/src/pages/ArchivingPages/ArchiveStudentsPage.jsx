import React, { useState, useMemo, useEffect } from "react";
import {
    Tabs, Card, Text, ScrollArea, Container, Title,
    Flex, Button, TextInput, MultiSelect, Grid, Loader,
    Paper, Center, Divider, Checkbox, Group,
    rem, Modal, Stack
} from "@mantine/core";
import { debounce } from "lodash";
import { showNotification } from "@mantine/notifications";
import { FaCheck, FaTimes } from "react-icons/fa";
import { fetchUsersByType, archiveUser } from "../../services/userService";
import { getAllDepartments, getDepartmentsByProgramme } from "../../services/roleService";
import { showErrorNotification, showSuccessNotification } from "../../utils/errorHandler";

const InfoCard = ({ person, selectable, selected, onSelectChange }) => (
    <Card shadow="sm" radius="xl" withBorder p="lg" style={{ backgroundColor: "#fdfdfd" }}>
        <Group position="apart" align="flex-start">
            <div style={{ flex: 1 }}>
                <Text fw={600} size="lg" mb="xs">{person.full_name}</Text>
                <Text size="sm" c="dimmed"><strong>Username:</strong> {person.username}</Text>
                <Divider my="sm" />
                <Text size="sm"><strong>Programme:</strong> {person.programme}</Text>
                <Text size="sm"><strong>Discipline:</strong> {person.discipline}</Text>
                <Text size="sm"><strong>Batch:</strong> {person.batch}</Text>
                <Text size="sm"><strong>Semester:</strong> {person.curr_semester_no}</Text>
                <Text size="sm"><strong>Category:</strong> {person.category}</Text>
                <Text size="sm"><strong>Gender:</strong> {person.gender}</Text>
            </div>
            {selectable && (
                <Checkbox
                    checked={selected}
                    onChange={() => onSelectChange(person.username)}
                    mt="sm"
                />
            )}
        </Group>
    </Card>
);

const extractUnique = (arr, key) =>
    [...new Set(arr.map((item) => key === "semester"
        ? String(item.curr_semester_no)
        : String(item[key])
    ))];

const filterAndSearch = (data, filters, searchQuery) =>
    data.filter((person) => {
        const matchSearch = person.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            person.username.toLowerCase().includes(searchQuery.toLowerCase());

        const matchFilters = Object.entries(filters).every(([key, values]) => {
            if (values.length === 0) return true;
            const value = key === "semester" ? String(person.curr_semester_no) : String(person[key]);
            return values.includes(value);
        });

        return matchSearch && matchFilters;
    });

const ArchiveStudentPage = () => {
    const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("archive");
    const [searchQuery, setSearchQuery] = useState("");
    const [filters, setFilters] = useState({
        programme: [], discipline: [], batch: [], category: [], semester: [], gender: []
    });
    const [selectedUsernames, setSelectedUsernames] = useState([]);
    const [modalOpened, setModalOpened] = useState(false);
    const [actionType, setActionType] = useState("");
    const [processingAction, setProcessingAction] = useState(false);
    const [personToAction, setPersonToAction] = useState(null);
    const [departments, setDepartments] = useState([]);
    const [loadingDepartments, setLoadingDepartments] = useState(false);

    const fetchStudents = async () => {
        setLoading(true);
        try {
            const data = await fetchUsersByType('student');
            console.log('Fetched students data:', data);
            setStudents(data || []);
        } catch (error) {
            console.error('Error fetching students:', error);
            showErrorNotification(error, 'Fetch Error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStudents();
        // Don't fetch departments separately - we'll extract disciplines from student data
    }, []);

    const fetchDepartments = async (programme) => {
        console.log('[ArchiveStudents] Fetching departments for programme:', programme);
        if (!programme) {
            setDepartments([]);
            return;
        }
        setLoadingDepartments(true);
        try {
            // Use the new getDepartmentsByProgramme function
            const data = await getDepartmentsByProgramme(programme);
            console.log('[ArchiveStudents] Fetched departments:', data);
            setDepartments(data || []);
        } catch (error) {
            console.error('Error fetching departments:', error);
            setDepartments([]);
        } finally {
            setLoadingDepartments(false);
        }
    };

    const handleProgrammeChange = (selectedProgrammes) => {
        setFilters((prev) => ({ ...prev, programme: selectedProgrammes, discipline: [] })); // Clear discipline when programme changes
    };

    const handleSearchChange = useMemo(() =>
        debounce((value) => setSearchQuery(value), 200), []);

    const filteredData = useMemo(() =>
        filterAndSearch(students, filters, searchQuery),
        [students, filters, searchQuery]
    );

    const isSelected = (username) => selectedUsernames.includes(username);
    const toggleSelect = (username) => {
        setSelectedUsernames((prev) =>
            prev.includes(username) ? prev.filter(u => u !== username) : [...prev, username]
        );
    };

    const selectAll = () => {
        setSelectedUsernames(filteredData.map(u => u.username));
    };

    const clearSelection = () => setSelectedUsernames([]);

    const handleAction = (type) => {
        setActionType(type);
        setModalOpened(true);
    };

    const confirmAction = async () => {
        setProcessingAction(true);
        try {
            for (const username of selectedUsernames) {
                await archiveUser(username);
            }

            showSuccessNotification(`${selectedUsernames.length} student(s) ${actionType === 'archive' ? 'archived' : 'restored'} successfully`);

            await fetchStudents();
            clearSelection();
            setModalOpened(false);
        } catch (error) {
            showErrorNotification(error, 'Action Failed');
        } finally {
            setProcessingAction(false);
        }
    };

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
                        Archive Students
                    </Title>
                </Button>
            </Flex>

            <Paper shadow="lg" p="xl" radius="xl" withBorder>
                {loading ? (
                    <Center style={{ minHeight: 400 }}>
                        <Stack align="center">
                            <Loader size="xl" color="blue" />
                            <Text color="dimmed">Loading students...</Text>
                        </Stack>
                    </Center>
                ) : (
                    <Tabs value={activeTab} onChange={setActiveTab} variant="pills" color="blue" radius="lg" keepMounted={false}>
                        <Tabs.List grow mb="lg">
                            <Tabs.Tab value="archive">ARCHIVE</Tabs.Tab>
                            <Tabs.Tab value="archived">ARCHIVED</Tabs.Tab>
                            <Tabs.Tab value="alumnis">ALUMNIS</Tabs.Tab>
                        </Tabs.List>

                        <Tabs.Panel value="archive">
                            <Grid mb="lg">
                                <Grid.Col span={12}>
                                    <TextInput
                                        placeholder="🔍 Search students"
                                        radius="md"
                                        onChange={(e) => handleSearchChange(e.currentTarget.value)}
                                    />
                                </Grid.Col>
                                {["programme", "discipline", "batch", "semester", "category", "gender"].map((key) => (
                                    <Grid.Col span={6} key={key}>
                                        {key === "programme" ? (
                                            <MultiSelect
                                                label="Programme"
                                                placeholder="Filter by programme"
                                                value={filters.programme}
                                                onChange={handleProgrammeChange}
                                                data={extractUnique(students, key)}
                                                radius="md"
                                                searchable
                                                clearable
                                            />
                                        ) : key === "discipline" ? (
                                            <MultiSelect
                                                label="Discipline"
                                                placeholder="Select department"
                                                value={filters.discipline}
                                                onChange={(value) => setFilters((prev) => ({ ...prev, discipline: value }))}
                                                data={extractUnique(students, 'discipline').filter(d => d && d !== 'null' && d !== 'undefined').map(d => ({ value: d, label: d }))}
                                                radius="md"
                                                searchable
                                                clearable
                                            />
                                        ) : (
                                            <MultiSelect
                                                label={key[0].toUpperCase() + key.slice(1)}
                                                placeholder={`Filter by ${key}`}
                                                value={filters[key]}
                                                onChange={(value) => setFilters((prev) => ({ ...prev, [key]: value }))}
                                                data={extractUnique(students, key)}
                                                radius="md"
                                                searchable
                                                clearable
                                            />
                                        )}
                                    </Grid.Col>
                                ))}
                            </Grid>

                            <Group mb="md">
                                <Button onClick={selectAll} variant="light">Select All</Button>
                                <Button onClick={clearSelection} variant="default">Clear Selection</Button>
                            </Group>

                            <ScrollArea h={400}>
                                <Grid>
                                    {filteredData.map((student) => (
                                        <Grid.Col span={12} key={student.username}>
                                            <InfoCard
                                                person={student}
                                                selectable
                                                selected={isSelected(student.username)}
                                                onSelectChange={toggleSelect}
                                            />
                                        </Grid.Col>
                                    ))}
                                </Grid>
                            </ScrollArea>

                            {selectedUsernames.length > 0 && (
                                <Group mt="lg" position="right">
                                    <Button color="blue" onClick={() => handleAction("archived")}>Archive</Button>
                                    <Button color="teal" onClick={() => handleAction("alumni")}>Alumni</Button>
                                </Group>
                            )}
                        </Tabs.Panel>

                        <Tabs.Panel value="archived">
                            <Title order={3} mb="md">Recently Archived</Title>
                            <Grid>
                                {students.filter(s => !s.is_active).slice(0, 10).map((s) => (
                                    <Grid.Col span={12} key={s.username}>
                                        <InfoCard person={s} />
                                    </Grid.Col>
                                ))}
                                {students.filter(s => !s.is_active).length === 0 && (
                                    <Grid.Col span={12}>
                                        <Text color="dimmed">No archived students found</Text>
                                    </Grid.Col>
                                )}
                            </Grid>
                        </Tabs.Panel>

                        <Tabs.Panel value="alumnis">
                            <Title order={3} mb="md">Recent Alumnis</Title>
                            <Grid>
                                {students.filter(s => !s.is_active).slice(0, 10).map((s) => (
                                    <Grid.Col span={12} key={s.username}>
                                        <InfoCard person={s} />
                                    </Grid.Col>
                                ))}
                                {students.filter(s => !s.is_active).length === 0 && (
                                    <Grid.Col span={12}>
                                        <Text color="dimmed">No alumni found</Text>
                                    </Grid.Col>
                                )}
                            </Grid>
                        </Tabs.Panel>
                    </Tabs>
                )}
            </Paper>

            <Modal
                opened={modalOpened}
                onClose={() => !processingAction && setModalOpened(false)}
                title={`Confirm Marking as ${actionType.toUpperCase()}`}
                closeOnClickOutside={!processingAction}
            >
                <Text size="sm">Are you sure you want to mark {selectedUsernames.length} selected student(s) as {actionType}?</Text>
                <Group mt="md" position="right">
                    <Button variant="light" onClick={() => setModalOpened(false)} disabled={processingAction}>Cancel</Button>
                    <Button color="blue" onClick={confirmAction} loading={processingAction}>
                        {processingAction ? 'Processing...' : 'Confirm'}
                    </Button>
                </Group>
            </Modal>
        </Container>
    );
};

export default ArchiveStudentPage;
