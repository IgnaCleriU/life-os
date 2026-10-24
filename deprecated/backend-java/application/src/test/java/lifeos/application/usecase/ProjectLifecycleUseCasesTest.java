package lifeos.application.usecase;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import java.util.UUID;
import lifeos.application.Change;
import lifeos.application.fakes.InMemoryProjectRepository;
import lifeos.application.fakes.InMemoryTaskRepository;
import lifeos.application.port.ProjectFilter;
import lifeos.domain.DomainValidationException;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotEmptyException;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.ProjectStatus;
import lifeos.domain.Task;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

/** Casos de uso de Project, con repositorios fake en memoria (sin DB ni mocks). */
class ProjectLifecycleUseCasesTest {

    private final InMemoryProjectRepository projectRepo = new InMemoryProjectRepository();
    private final InMemoryTaskRepository taskRepo = new InMemoryTaskRepository();

    private Project seedProject(String description) {
        Project project = Project.create("Life OS", description);
        projectRepo.add(project);
        return project;
    }

    @Nested
    class CreateProjectTest {

        @Test
        void persistsAndReturnsProject() {
            Project project = new CreateProject(projectRepo)
                    .execute("Life OS", "Sistema operativo personal");

            assertThat(project.name()).isEqualTo("Life OS");
            assertThat(project.description()).isEqualTo("Sistema operativo personal");
            assertThat(project.status()).isSameAs(ProjectStatus.ACTIVE);
            assertThat(projectRepo.get(project.id())).containsSame(project);
        }

        @Test
        void withoutDescriptionDefaultsToNull() {
            assertThat(new CreateProject(projectRepo).execute("Sin descripción", null).description())
                    .isNull();
        }

        @ParameterizedTest
        @ValueSource(strings = {"", "   "})
        void withEmptyNameThrowsAndPersistsNothing(String invalidName) {
            assertThatThrownBy(() -> new CreateProject(projectRepo).execute(invalidName, null))
                    .isInstanceOf(DomainValidationException.class);
            assertThat(projectRepo.list(ProjectFilter.all())).isEmpty();
        }
    }

    @Nested
    class ListProjectsTest {

        @Test
        void emptyRepoReturnsEmptyList() {
            assertThat(new ListProjects(projectRepo).execute(ProjectFilter.all())).isEmpty();
        }

        @Test
        void returnsAllCreatedProjects() {
            var create = new CreateProject(projectRepo);
            var created = List.of(
                    create.execute("Proyecto 0", null),
                    create.execute("Proyecto 1", null),
                    create.execute("Proyecto 2", null));

            assertThat(new ListProjects(projectRepo).execute(ProjectFilter.all()))
                    .containsExactlyInAnyOrderElementsOf(created);
        }

        @Test
        void filtersByStatus() {
            Project activo = Project.create("Activo", null);
            Project archivado = Project.create("Archivado", null);
            archivado.archive();
            projectRepo.add(activo);
            projectRepo.add(archivado);

            var result = new ListProjects(projectRepo)
                    .execute(ProjectFilter.all().withStatuses(List.of(ProjectStatus.ARCHIVED)));

            assertThat(result).containsExactly(archivado);
        }

        @Test
        void filtersByTextCaseInsensitively() {
            Project casa = Project.create("Casa de campo", null);
            projectRepo.add(casa);
            projectRepo.add(Project.create("Finanzas", null));

            var result = new ListProjects(projectRepo).execute(ProjectFilter.all().matching("CASA"));

            assertThat(result).containsExactly(casa);
        }
    }

    @Nested
    class GetProjectTest {

        @Test
        void returnsTheProject() {
            Project project = seedProject(null);

            assertThat(new GetProject(projectRepo).execute(project.id())).isSameAs(project);
        }

        @Test
        void missingProjectThrows() {
            assertThatThrownBy(() -> new GetProject(projectRepo).execute(UUID.randomUUID()))
                    .isInstanceOf(ProjectNotFoundException.class);
        }

        @Test
        void deletedProjectThrows() {
            Project project = seedProject(null);
            new DeleteProject(projectRepo, taskRepo).execute(project.id());

            assertThatThrownBy(() -> new GetProject(projectRepo).execute(project.id()))
                    .isInstanceOf(ProjectNotFoundException.class);
        }
    }

    @Nested
    class UpdateProjectTest {

        @Test
        void renamesAndPersists() {
            Project project = seedProject(null);

            Project updated = new UpdateProject(projectRepo)
                    .execute(project.id(), "Life OS v2", Change.unset());

            assertThat(updated.name()).isEqualTo("Life OS v2");
            assertThat(projectRepo.get(project.id()).orElseThrow().name()).isEqualTo("Life OS v2");
        }

        @Test
        void setsDescription() {
            Project project = seedProject(null);

            Project updated = new UpdateProject(projectRepo)
                    .execute(project.id(), null, Change.to("Sistema operativo personal"));

            assertThat(updated.description()).isEqualTo("Sistema operativo personal");
        }

        @Test
        void clearsDescriptionWithExplicitNull() {
            Project project = seedProject("original");

            Project updated = new UpdateProject(projectRepo)
                    .execute(project.id(), null, Change.to(null));

            assertThat(updated.description()).isNull();
        }

        @Test
        void leavesDescriptionUntouchedWhenUnset() {
            Project project = seedProject("original");

            Project updated = new UpdateProject(projectRepo)
                    .execute(project.id(), "Otro nombre", Change.unset());

            assertThat(updated.description()).isEqualTo("original");
        }

        @Test
        void withEmptyNameThrows() {
            Project project = seedProject(null);

            assertThatThrownBy(() -> new UpdateProject(projectRepo)
                            .execute(project.id(), "   ", Change.unset()))
                    .isInstanceOf(DomainValidationException.class);
        }

        @Test
        void missingProjectThrows() {
            assertThatThrownBy(() -> new UpdateProject(projectRepo)
                            .execute(UUID.randomUUID(), "X", Change.unset()))
                    .isInstanceOf(ProjectNotFoundException.class);
        }
    }

    @Nested
    class StatusTransitionsTest {

        @Test
        void completeMarksCompletedAndPersists() {
            Project project = seedProject(null);

            assertThat(new CompleteProject(projectRepo).execute(project.id()).status())
                    .isSameAs(ProjectStatus.COMPLETED);
            assertThat(projectRepo.get(project.id()).orElseThrow().status())
                    .isSameAs(ProjectStatus.COMPLETED);
        }

        @Test
        void archiveMarksArchivedAndPersists() {
            Project project = seedProject(null);

            assertThat(new ArchiveProject(projectRepo).execute(project.id()).status())
                    .isSameAs(ProjectStatus.ARCHIVED);
            assertThat(projectRepo.get(project.id()).orElseThrow().status())
                    .isSameAs(ProjectStatus.ARCHIVED);
        }

        @Test
        void activateReturnsToActiveAndPersists() {
            Project project = seedProject(null);
            new ArchiveProject(projectRepo).execute(project.id());

            assertThat(new ActivateProject(projectRepo).execute(project.id()).status())
                    .isSameAs(ProjectStatus.ACTIVE);
            assertThat(projectRepo.get(project.id()).orElseThrow().status())
                    .isSameAs(ProjectStatus.ACTIVE);
        }

        @Test
        void transitionOnMissingProjectThrows() {
            UUID missing = UUID.randomUUID();

            assertThatThrownBy(() -> new CompleteProject(projectRepo).execute(missing))
                    .isInstanceOf(ProjectNotFoundException.class);
            assertThatThrownBy(() -> new ArchiveProject(projectRepo).execute(missing))
                    .isInstanceOf(ProjectNotFoundException.class);
            assertThatThrownBy(() -> new ActivateProject(projectRepo).execute(missing))
                    .isInstanceOf(ProjectNotFoundException.class);
        }
    }

    /**
     * El borrado de proyectos no cascadea: un proyecto con tareas vivas no se
     * borra. Arrastrar las tareas obligaría a {@code RestoreProject} a recordar
     * cuáles se llevó.
     */
    @Nested
    class DeleteAndRestoreProjectTest {

        @Test
        void deleteEmptyProjectMarksItAndHidesItFromListings() {
            Project project = seedProject(null);

            Project deleted = new DeleteProject(projectRepo, taskRepo).execute(project.id());

            assertThat(deleted.isDeleted()).isTrue();
            assertThat(projectRepo.get(project.id())).isEmpty();
            assertThat(new ListProjects(projectRepo).execute(ProjectFilter.all())).isEmpty();
        }

        @Test
        void deleteProjectWithLiveTasksThrowsAndChangesNothing() {
            Project project = seedProject(null);
            taskRepo.add(Task.create(project.id(), "Tarea viva"));

            assertThatThrownBy(() -> new DeleteProject(projectRepo, taskRepo).execute(project.id()))
                    .isInstanceOf(ProjectNotEmptyException.class);
            assertThat(projectRepo.get(project.id())).isPresent();
        }

        @Test
        void deleteSucceedsOnceItsTasksAreDeleted() {
            Project project = seedProject(null);
            Task task = Task.create(project.id(), "Tarea");
            taskRepo.add(task);
            new DeleteTask(taskRepo).execute(task.id());

            assertThat(new DeleteProject(projectRepo, taskRepo).execute(project.id()).isDeleted())
                    .isTrue();
        }

        @Test
        void deleteIgnoresTasksOfOtherProjects() {
            Project project = seedProject(null);
            taskRepo.add(Task.create(UUID.randomUUID(), "Tarea ajena"));

            assertThat(new DeleteProject(projectRepo, taskRepo).execute(project.id()).isDeleted())
                    .isTrue();
        }

        @Test
        void deleteMissingProjectThrows() {
            assertThatThrownBy(() -> new DeleteProject(projectRepo, taskRepo).execute(UUID.randomUUID()))
                    .isInstanceOf(ProjectNotFoundException.class);
        }

        @Test
        void restoreBringsTheProjectBack() {
            Project project = seedProject(null);
            new DeleteProject(projectRepo, taskRepo).execute(project.id());

            Project restored = new RestoreProject(projectRepo).execute(project.id());

            assertThat(restored.isDeleted()).isFalse();
            assertThat(new ListProjects(projectRepo).execute(ProjectFilter.all()))
                    .containsExactly(restored);
        }

        @Test
        void restoreMissingProjectThrows() {
            assertThatThrownBy(() -> new RestoreProject(projectRepo).execute(UUID.randomUUID()))
                    .isInstanceOf(ProjectNotFoundException.class);
        }
    }
}
