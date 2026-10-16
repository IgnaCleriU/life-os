package lifeos.infrastructure.db;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.nio.file.Path;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import lifeos.application.port.TaskFilter;
import lifeos.domain.Priority;
import lifeos.domain.Project;
import lifeos.domain.Task;
import lifeos.domain.TaskStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.dao.DataIntegrityViolationException;

class SqliteTaskRepositoryTest {

    @TempDir
    Path tmp;

    private TestDatabase db;
    private SqliteTaskRepository repo;

    @BeforeEach
    void setUp() {
        db = new TestDatabase(tmp);
        repo = db.tasks();
    }

    private Project addProject(String name) {
        Project project = Project.create(name, null);
        db.projects().add(project);
        return project;
    }

    private static List<UUID> ids(List<Task> tasks) {
        return tasks.stream().map(Task::id).toList();
    }

    @Test
    void addGetAndListFilteredByProject() {
        Project project = addProject("Proyecto");
        Project other = addProject("Otro");
        Task task = Task.create(project.id(), "Tarea", Priority.HIGH, LocalDate.of(2026, 8, 1), "detalle");
        repo.add(task);
        repo.add(Task.create(other.id(), "Ajena"));

        Task loaded = repo.get(task.id()).orElseThrow();
        assertThat(loaded.projectId()).isEqualTo(project.id());
        assertThat(loaded.title()).isEqualTo("Tarea");
        assertThat(loaded.description()).isEqualTo("detalle");
        assertThat(loaded.status()).isSameAs(TaskStatus.TODO);
        assertThat(loaded.priority()).isSameAs(Priority.HIGH);
        assertThat(loaded.dueDate()).isEqualTo(LocalDate.of(2026, 8, 1));
        assertThat(loaded.createdAt()).isEqualTo(task.createdAt());
        assertThat(ids(repo.list(TaskFilter.all().inProject(project.id())))).containsExactly(task.id());
    }

    @Test
    void getMissingReturnsEmpty() {
        assertThat(repo.get(UUID.randomUUID())).isEmpty();
    }

    @Test
    void listEmpty() {
        assertThat(repo.list(TaskFilter.all())).isEmpty();
    }

    @Test
    void updatePersistsStatusChange() {
        Task task = Task.create(addProject("P").id(), "Tarea");
        repo.add(task);

        task.complete();
        repo.update(task);

        assertThat(repo.get(task.id()).orElseThrow().status()).isSameAs(TaskStatus.DONE);
    }

    @Test
    void updatePersistsAllMutableFields() {
        Task task = Task.create(addProject("P").id(), "Tarea", Priority.LOW, LocalDate.of(2026, 8, 1), "x");
        repo.add(task);

        task.rename("Tarea renombrada");
        task.changePriority(Priority.HIGH);
        task.reschedule(null);
        task.describe(null);
        repo.update(task);

        Task reloaded = repo.get(task.id()).orElseThrow();
        assertThat(reloaded.title()).isEqualTo("Tarea renombrada");
        assertThat(reloaded.priority()).isSameAs(Priority.HIGH);
        assertThat(reloaded.dueDate()).isNull();
        assertThat(reloaded.description()).isNull();
    }

    @Test
    void updatePersistsMoveToAnotherProject() {
        Task task = Task.create(addProject("Origen").id(), "Tarea");
        repo.add(task);
        Project destino = addProject("Destino");

        task.moveTo(destino.id());
        repo.update(task);

        assertThat(repo.get(task.id()).orElseThrow().projectId()).isEqualTo(destino.id());
    }

    @Test
    void addRejectsTaskWithUnknownProjectId() {
        Task task = Task.create(UUID.randomUUID(), "Tarea huérfana");

        assertThatThrownBy(() -> repo.add(task)).isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void deletedTaskIsInvisibleToGetAndList() {
        Task task = Task.create(addProject("P").id(), "Tarea");
        repo.add(task);

        task.delete();
        repo.update(task);

        assertThat(repo.get(task.id())).isEmpty();
        assertThat(repo.list(TaskFilter.all())).isEmpty();
    }

    @Test
    void deletedTaskIsReachableWithIncludeDeleted() {
        Task task = Task.create(addProject("P").id(), "Tarea");
        repo.add(task);
        task.delete();
        repo.update(task);

        Task loaded = repo.get(task.id(), true).orElseThrow();

        assertThat(loaded.deletedAt()).isEqualTo(task.deletedAt());
    }

    @Test
    void restoreMakesTheTaskVisibleAgain() {
        Task task = Task.create(addProject("P").id(), "Tarea");
        repo.add(task);
        task.delete();
        repo.update(task);

        task.restore();
        repo.update(task);

        assertThat(repo.get(task.id())).isPresent();
    }

    @Test
    void listFiltersByStatus() {
        Project project = addProject("P");
        Task todo = Task.create(project.id(), "Pendiente");
        Task done = Task.create(project.id(), "Hecha");
        done.complete();
        repo.add(todo);
        repo.add(done);

        assertThat(ids(repo.list(TaskFilter.all().withStatuses(List.of(TaskStatus.DONE)))))
                .containsExactly(done.id());
        assertThat(ids(repo.list(TaskFilter.all().withStatuses(List.of(TaskStatus.TODO, TaskStatus.DONE)))))
                .containsExactly(todo.id(), done.id());
        assertThat(repo.list(TaskFilter.all().withStatuses(List.of()))).isEmpty();
    }

    @Test
    void listFiltersByDueBeforeInclusiveAndExcludesUndated() {
        Project project = addProject("P");
        Task vencida = Task.create(project.id(), "Vencida", Priority.MEDIUM, LocalDate.of(2026, 7, 1), null);
        Task futura = Task.create(project.id(), "Futura", Priority.MEDIUM, LocalDate.of(2026, 12, 1), null);
        Task sinFecha = Task.create(project.id(), "Sin fecha");
        repo.add(vencida);
        repo.add(futura);
        repo.add(sinFecha);

        assertThat(ids(repo.list(TaskFilter.all().dueOnOrBefore(LocalDate.of(2026, 7, 28)))))
                .containsExactly(vencida.id());
        assertThat(ids(repo.list(TaskFilter.all().dueOnOrBefore(LocalDate.of(2026, 7, 1)))))
                .containsExactly(vencida.id());
    }

    @Test
    void listFiltersByTextCaseInsensitively() {
        Project project = addProject("P");
        Task expensas = Task.create(project.id(), "Pagar Expensas");
        repo.add(expensas);
        repo.add(Task.create(project.id(), "Renovar seguro"));

        assertThat(ids(repo.list(TaskFilter.all().matching("expENSAS")))).containsExactly(expensas.id());
    }
}
