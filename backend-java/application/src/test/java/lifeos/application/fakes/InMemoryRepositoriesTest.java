package lifeos.application.fakes;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.UUID;
import lifeos.application.port.ProjectFilter;
import lifeos.application.port.TaskFilter;
import lifeos.domain.Project;
import lifeos.domain.Task;
import org.junit.jupiter.api.Test;

/** Tests de los repositorios fake en memoria usados por el resto de la suite. */
class InMemoryRepositoriesTest {

    @Test
    void projectRepoAddGetAndList() {
        var repo = new InMemoryProjectRepository();
        Project project = Project.create("Life OS", null);

        repo.add(project);

        assertThat(repo.get(project.id())).containsSame(project);
        assertThat(repo.list(ProjectFilter.all())).containsExactly(project);
    }

    @Test
    void projectRepoGetMissingReturnsEmpty() {
        assertThat(new InMemoryProjectRepository().get(UUID.randomUUID())).isEmpty();
    }

    @Test
    void taskRepoAddGetAndListFilteredByProject() {
        var repo = new InMemoryTaskRepository();
        UUID projectId = UUID.randomUUID();
        Task task = Task.create(projectId, "Escribir ports");
        Task other = Task.create(UUID.randomUUID(), "Tarea de otro proyecto");
        repo.add(task);
        repo.add(other);

        assertThat(repo.get(task.id())).containsSame(task);
        assertThat(repo.list(TaskFilter.all().inProject(projectId))).containsExactly(task);
    }

    @Test
    void taskRepoUpdatePersistsChanges() {
        var repo = new InMemoryTaskRepository();
        Task task = Task.create(UUID.randomUUID(), "Tarea");
        repo.add(task);

        task.complete();
        repo.update(task);

        assertThat(repo.get(task.id()).orElseThrow().status()).isSameAs(task.status());
    }
}
