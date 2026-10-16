package lifeos.infrastructure.db;

import static org.assertj.core.api.Assertions.assertThat;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import lifeos.application.port.ProjectFilter;
import lifeos.application.port.TaskFilter;
import lifeos.domain.Project;
import lifeos.domain.Task;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Guarda de contrato: la exclusión de borrados vive en los repositorios.
 *
 * <p>Olvidar el filtro en un método nuevo es un bug silencioso: nada falla,
 * simplemente reaparece algo que el usuario borró. Estos tests verifican
 * <i>cobertura</i>: si alguien agrega un método público a un repositorio, fallan
 * hasta que se lo agregue acá con su caso de borrado escrito. La lista blanca es
 * deliberadamente molesta de actualizar.
 */
class SoftDeleteContractTest {

    private static final Set<String> EXPECTED_PUBLIC_METHODS = Set.of("add", "get", "list", "update");

    @TempDir
    Path tmp;

    @ParameterizedTest
    @ValueSource(classes = {SqliteTaskRepository.class, SqliteProjectRepository.class})
    void repositorySurfaceIsFullyAuditedForSoftDelete(Class<?> repoClass) {
        Set<String> publicMethods = Arrays.stream(repoClass.getDeclaredMethods())
                .filter(method -> Modifier.isPublic(method.getModifiers()))
                .filter(method -> !method.isSynthetic())
                .map(Method::getName)
                .collect(Collectors.toSet());

        assertThat(publicMethods)
                .as("%s cambió su superficie pública. Antes de tocar esta lista, escribí el test "
                        + "que verifica que el método nuevo excluye los registros borrados.",
                        repoClass.getSimpleName())
                .isEqualTo(EXPECTED_PUBLIC_METHODS);
    }

    @Test
    void everyTaskReadPathHidesDeletedRows() {
        var db = new TestDatabase(tmp);
        Project project = Project.create("Proyecto", null);
        db.projects().add(project);
        var repo = db.tasks();
        Task task = Task.create(project.id(), "Tarea");
        repo.add(task);
        task.delete();
        repo.update(task);

        assertThat(repo.get(task.id())).isEmpty();
        assertThat(repo.list(TaskFilter.all())).isEmpty();
        assertThat(repo.list(TaskFilter.all().inProject(project.id()))).isEmpty();
        assertThat(repo.list(TaskFilter.all().withStatuses(List.of(task.status())))).isEmpty();
        assertThat(repo.list(TaskFilter.all().matching("Tarea"))).isEmpty();
    }

    @Test
    void everyProjectReadPathHidesDeletedRows() {
        var repo = new TestDatabase(tmp).projects();
        Project project = Project.create("Proyecto", null);
        repo.add(project);
        project.delete();
        repo.update(project);

        assertThat(repo.get(project.id())).isEmpty();
        assertThat(repo.list(ProjectFilter.all())).isEmpty();
        assertThat(repo.list(ProjectFilter.all().withStatuses(List.of(project.status())))).isEmpty();
        assertThat(repo.list(ProjectFilter.all().matching("Proyecto"))).isEmpty();
    }
}
