package lifeos.application.usecase;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import lifeos.application.fakes.InMemoryProjectRepository;
import lifeos.application.fakes.InMemoryTaskRepository;
import lifeos.application.port.TaskFilter;
import lifeos.domain.DomainValidationException;
import lifeos.domain.Priority;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;
import lifeos.domain.TaskStatus;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

/** Casos de uso de Task, con repositorios fake en memoria (sin DB ni mocks). */
class TaskLifecycleUseCasesTest {

    private final InMemoryProjectRepository projectRepo = new InMemoryProjectRepository();
    private final InMemoryTaskRepository taskRepo = new InMemoryTaskRepository();

    private Project seedProject(String name) {
        Project project = Project.create(name, null);
        projectRepo.add(project);
        return project;
    }

    private Task seedTask() {
        Task task = Task.create(seedProject("Proyecto").id(), "Tarea");
        taskRepo.add(task);
        return task;
    }

    @Nested
    class CreateTaskTest {

        @Test
        void underExistingProjectPersistsIt() {
            Project project = seedProject("Life OS");

            Task task = new CreateTask(taskRepo, projectRepo)
                    .execute(project.id(), "Escribir tests", Priority.HIGH, null, null);

            assertThat(task.projectId()).isEqualTo(project.id());
            assertThat(task.title()).isEqualTo("Escribir tests");
            assertThat(task.priority()).isSameAs(Priority.HIGH);
            assertThat(task.status()).isSameAs(TaskStatus.TODO);
            assertThat(taskRepo.get(task.id())).containsSame(task);
        }

        @Test
        void withoutPriorityDefaultsToMedium() {
            Project project = seedProject("Life OS");

            Task task = new CreateTask(taskRepo, projectRepo).execute(project.id(), "Tarea", null, null, null);

            assertThat(task.priority()).isSameAs(Priority.MEDIUM);
        }

        @Test
        void underMissingProjectThrows() {
            assertThatThrownBy(() -> new CreateTask(taskRepo, projectRepo)
                            .execute(UUID.randomUUID(), "Tarea huérfana", Priority.MEDIUM, null, null))
                    .isInstanceOf(ProjectNotFoundException.class);
        }

        @Test
        void withEmptyTitleThrows() {
            Project project = seedProject("Life OS");

            assertThatThrownBy(() -> new CreateTask(taskRepo, projectRepo)
                            .execute(project.id(), "   ", Priority.MEDIUM, null, null))
                    .isInstanceOf(DomainValidationException.class);
        }
    }

    @Nested
    class ListTasksTest {

        private final UUID projectId = UUID.randomUUID();
        private Task vencida;
        private Task sinFecha;
        private Task hecha;

        /** Cuatro tareas del mismo proyecto, una por combinación a filtrar. */
        private ListTasks seedFilterable() {
            vencida = Task.create(projectId, "Pagar expensas", Priority.MEDIUM, LocalDate.of(2026, 7, 1), null);
            Task futura = Task.create(projectId, "Renovar seguro", Priority.MEDIUM, LocalDate.of(2026, 12, 1), null);
            sinFecha = Task.create(projectId, "Leer sobre expensas");
            hecha = Task.create(projectId, "Tarea hecha");
            hecha.complete();
            for (Task task : List.of(vencida, futura, sinFecha, hecha)) {
                taskRepo.add(task);
            }
            return new ListTasks(taskRepo);
        }

        @Test
        void returnsOnlyTasksOfGivenProject() {
            UUID projectA = UUID.randomUUID();
            Task a1 = Task.create(projectA, "A1");
            Task a2 = Task.create(projectA, "A2");
            taskRepo.add(a1);
            taskRepo.add(a2);
            taskRepo.add(Task.create(UUID.randomUUID(), "B1"));

            assertThat(new ListTasks(taskRepo).execute(TaskFilter.all().inProject(projectA)))
                    .containsExactlyInAnyOrder(a1, a2);
        }

        @Test
        void emptyProjectReturnsEmptyList() {
            assertThat(new ListTasks(taskRepo).execute(TaskFilter.all().inProject(UUID.randomUUID())))
                    .isEmpty();
        }

        @Test
        void withoutProjectReturnsTasksAcrossProjects() {
            Task una = Task.create(UUID.randomUUID(), "Una");
            Task otra = Task.create(UUID.randomUUID(), "Otra");
            taskRepo.add(una);
            taskRepo.add(otra);

            assertThat(new ListTasks(taskRepo).execute(TaskFilter.all()))
                    .containsExactlyInAnyOrder(una, otra);
        }

        @Test
        void filtersByStatus() {
            var useCase = seedFilterable();

            assertThat(useCase.execute(TaskFilter.all().inProject(projectId)
                            .withStatuses(List.of(TaskStatus.DONE))))
                    .containsExactly(hecha);
        }

        @Test
        void filtersByDueBeforeAndExcludesUndatedTasks() {
            var useCase = seedFilterable();

            assertThat(useCase.execute(TaskFilter.all().inProject(projectId)
                            .dueOnOrBefore(LocalDate.of(2026, 7, 28))))
                    .containsExactly(vencida);
        }

        @Test
        void dueBeforeIsInclusive() {
            var useCase = seedFilterable();

            assertThat(useCase.execute(TaskFilter.all().inProject(projectId)
                            .dueOnOrBefore(LocalDate.of(2026, 7, 1))))
                    .contains(vencida);
        }

        @Test
        void filtersByTextCaseInsensitively() {
            var useCase = seedFilterable();

            assertThat(useCase.execute(TaskFilter.all().inProject(projectId).matching("EXPENSAS")))
                    .containsExactlyInAnyOrder(vencida, sinFecha);
        }

        @Test
        void combinesFiltersWithAnd() {
            var useCase = seedFilterable();

            assertThat(useCase.execute(TaskFilter.all().inProject(projectId)
                            .withStatuses(List.of(TaskStatus.TODO))
                            .matching("expensas")
                            .dueOnOrBefore(LocalDate.of(2026, 7, 28))))
                    .containsExactly(vencida);
        }
    }

    @Nested
    class GetTaskTest {

        @Test
        void returnsTheTask() {
            Task task = seedTask();

            assertThat(new GetTask(taskRepo).execute(task.id())).isSameAs(task);
        }

        @Test
        void missingTaskThrows() {
            assertThatThrownBy(() -> new GetTask(taskRepo).execute(UUID.randomUUID()))
                    .isInstanceOf(TaskNotFoundException.class);
        }

        @Test
        void deletedTaskThrows() {
            Task task = seedTask();
            new DeleteTask(taskRepo).execute(task.id());

            assertThatThrownBy(() -> new GetTask(taskRepo).execute(task.id()))
                    .isInstanceOf(TaskNotFoundException.class);
        }
    }

    @Nested
    class UpdateTaskTest {

        private Task seed(LocalDate dueDate, String description) {
            Task task = Task.create(UUID.randomUUID(), "Tarea", Priority.MEDIUM, dueDate, description);
            taskRepo.add(task);
            return task;
        }

        @Test
        void updatesTitleAndPriority() {
            Task task = seed(null, null);

            Task updated = new UpdateTask(taskRepo).execute(task.id(),
                    TaskUpdate.none().withTitle("Nuevo título").withPriority(Priority.HIGH));

            assertThat(updated.title()).isEqualTo("Nuevo título");
            assertThat(updated.priority()).isSameAs(Priority.HIGH);
            assertThat(taskRepo.get(task.id()).orElseThrow().title()).isEqualTo("Nuevo título");
        }

        @Test
        void setsDueDate() {
            Task task = seed(null, null);
            LocalDate due = LocalDate.of(2026, 8, 1);

            assertThat(new UpdateTask(taskRepo).execute(task.id(), TaskUpdate.none().withDueDate(due))
                            .dueDate())
                    .isEqualTo(due);
        }

        @Test
        void clearsDueDateWithExplicitNull() {
            Task task = seed(LocalDate.of(2026, 8, 1), null);

            assertThat(new UpdateTask(taskRepo).execute(task.id(), TaskUpdate.none().withDueDate(null))
                            .dueDate())
                    .isNull();
        }

        @Test
        void leavesDueDateUnchangedWhenUnset() {
            LocalDate due = LocalDate.of(2026, 8, 1);
            Task task = seed(due, null);

            assertThat(new UpdateTask(taskRepo).execute(task.id(),
                            TaskUpdate.none().withTitle("Solo título")).dueDate())
                    .isEqualTo(due);
        }

        @Test
        void missingTaskThrows() {
            assertThatThrownBy(() -> new UpdateTask(taskRepo)
                            .execute(UUID.randomUUID(), TaskUpdate.none().withTitle("No existe")))
                    .isInstanceOf(TaskNotFoundException.class);
        }

        @Test
        void setsDescription() {
            Task task = seed(null, null);

            assertThat(new UpdateTask(taskRepo).execute(task.id(),
                            TaskUpdate.none().withDescription("Detalle largo")).description())
                    .isEqualTo("Detalle largo");
        }

        @Test
        void clearsDescriptionWithExplicitNull() {
            Task task = seed(null, "original");

            assertThat(new UpdateTask(taskRepo).execute(task.id(),
                            TaskUpdate.none().withDescription(null)).description())
                    .isNull();
        }

        @Test
        void leavesDescriptionUntouchedWhenUnset() {
            Task task = seed(null, "original");

            assertThat(new UpdateTask(taskRepo).execute(task.id(),
                            TaskUpdate.none().withTitle("Otro título")).description())
                    .isEqualTo("original");
        }
    }

    @Nested
    class StatusTransitionsTest {

        @Test
        void completeMarksDoneAndPersists() {
            Task task = seedTask();

            assertThat(new CompleteTask(taskRepo).execute(task.id()).status()).isSameAs(TaskStatus.DONE);
            assertThat(taskRepo.get(task.id()).orElseThrow().status()).isSameAs(TaskStatus.DONE);
        }

        @Test
        void startMarksDoingAndPersists() {
            Task task = seedTask();

            assertThat(new StartTask(taskRepo).execute(task.id()).status()).isSameAs(TaskStatus.DOING);
            assertThat(taskRepo.get(task.id()).orElseThrow().status()).isSameAs(TaskStatus.DOING);
        }

        @Test
        void reopenReturnsToTodoAndPersists() {
            Task task = seedTask();
            task.complete();
            taskRepo.update(task);

            assertThat(new ReopenTask(taskRepo).execute(task.id()).status()).isSameAs(TaskStatus.TODO);
            assertThat(taskRepo.get(task.id()).orElseThrow().status()).isSameAs(TaskStatus.TODO);
        }

        @Test
        void transitionOnMissingTaskThrows() {
            UUID missing = UUID.randomUUID();

            assertThatThrownBy(() -> new CompleteTask(taskRepo).execute(missing))
                    .isInstanceOf(TaskNotFoundException.class);
            assertThatThrownBy(() -> new StartTask(taskRepo).execute(missing))
                    .isInstanceOf(TaskNotFoundException.class);
            assertThatThrownBy(() -> new ReopenTask(taskRepo).execute(missing))
                    .isInstanceOf(TaskNotFoundException.class);
        }
    }

    @Nested
    class MoveTaskTest {

        @Test
        void reassignsProjectAndPersists() {
            Task task = seedTask();
            Project destino = seedProject("Destino");

            Task moved = new MoveTask(taskRepo, projectRepo).execute(task.id(), destino.id());

            assertThat(moved.projectId()).isEqualTo(destino.id());
            assertThat(taskRepo.get(task.id()).orElseThrow().projectId()).isEqualTo(destino.id());
        }

        @Test
        void missingTaskThrows() {
            Project destino = seedProject("Destino");

            assertThatThrownBy(() -> new MoveTask(taskRepo, projectRepo)
                            .execute(UUID.randomUUID(), destino.id()))
                    .isInstanceOf(TaskNotFoundException.class);
        }

        @Test
        void toMissingProjectThrowsAndLeavesTaskUntouched() {
            Task task = seedTask();
            UUID proyectoOriginal = task.projectId();

            assertThatThrownBy(() -> new MoveTask(taskRepo, projectRepo)
                            .execute(task.id(), UUID.randomUUID()))
                    .isInstanceOf(ProjectNotFoundException.class);
            assertThat(taskRepo.get(task.id()).orElseThrow().projectId()).isEqualTo(proyectoOriginal);
        }
    }

    /**
     * DeleteTask y RestoreTask sostienen {@code dd} y {@code u} en la TUI: el
     * borrado es lógico para que restaurar sea un cambio de campo.
     */
    @Nested
    class DeleteAndRestoreTaskTest {

        @Test
        void deleteMarksTheTaskAndHidesItFromListings() {
            Task task = seedTask();

            Task deleted = new DeleteTask(taskRepo).execute(task.id());

            assertThat(deleted.isDeleted()).isTrue();
            assertThat(taskRepo.get(task.id())).isEmpty();
            assertThat(new ListTasks(taskRepo).execute(TaskFilter.all().inProject(task.projectId())))
                    .isEmpty();
        }

        @Test
        void deleteMissingTaskThrows() {
            assertThatThrownBy(() -> new DeleteTask(taskRepo).execute(UUID.randomUUID()))
                    .isInstanceOf(TaskNotFoundException.class);
        }

        @Test
        void restoreBringsTheTaskBack() {
            Task task = seedTask();
            new DeleteTask(taskRepo).execute(task.id());

            Task restored = new RestoreTask(taskRepo, projectRepo).execute(task.id());

            assertThat(restored.isDeleted()).isFalse();
            assertThat(new ListTasks(taskRepo).execute(TaskFilter.all().inProject(task.projectId())))
                    .containsExactly(restored);
        }

        @Test
        void restoreMissingTaskThrows() {
            assertThatThrownBy(() -> new RestoreTask(taskRepo, projectRepo).execute(UUID.randomUUID()))
                    .isInstanceOf(TaskNotFoundException.class);
        }

        @Test
        void restoreUnderDeletedProjectThrowsAndLeavesItDeleted() {
            // Borrar la única tarea deja el proyecto vacío y borrable; restaurar
            // la tarea después no debe reflotarla colgada de un proyecto invisible.
            Task task = seedTask();
            new DeleteTask(taskRepo).execute(task.id());
            new DeleteProject(projectRepo, taskRepo).execute(task.projectId());

            assertThatThrownBy(() -> new RestoreTask(taskRepo, projectRepo).execute(task.id()))
                    .isInstanceOf(ProjectNotFoundException.class);
            assertThat(taskRepo.get(task.id())).isEmpty();
        }

        @Test
        void restoreUnderMissingProjectThrows() {
            Task task = Task.create(UUID.randomUUID(), "Huérfana");
            taskRepo.add(task);
            new DeleteTask(taskRepo).execute(task.id());

            assertThatThrownBy(() -> new RestoreTask(taskRepo, projectRepo).execute(task.id()))
                    .isInstanceOf(ProjectNotFoundException.class);
        }

        @Test
        void deleteThenRestorePreservesEveryField() {
            Task task = seedTask();
            task.complete();
            taskRepo.update(task);
            new DeleteTask(taskRepo).execute(task.id());

            Task restored = new RestoreTask(taskRepo, projectRepo).execute(task.id());

            assertThat(restored.title()).isEqualTo(task.title());
            assertThat(restored.status()).isEqualTo(task.status());
            assertThat(restored.priority()).isEqualTo(task.priority());
        }
    }
}
