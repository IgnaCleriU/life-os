package lifeos.infrastructure.db;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.nio.file.Path;
import java.util.List;
import java.util.UUID;
import lifeos.application.port.ProjectFilter;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.ProjectStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class SqliteProjectRepositoryTest {

    @TempDir
    Path tmp;

    private SqliteProjectRepository repo;

    @BeforeEach
    void setUp() {
        repo = new TestDatabase(tmp).projects();
    }

    private static List<UUID> ids(List<Project> projects) {
        return projects.stream().map(Project::id).toList();
    }

    @Test
    void addGetAndList() {
        Project project = Project.create("Life OS", "Sistema operativo personal");

        repo.add(project);

        Project loaded = repo.get(project.id()).orElseThrow();
        assertThat(loaded.id()).isEqualTo(project.id());
        assertThat(loaded.name()).isEqualTo("Life OS");
        assertThat(loaded.description()).isEqualTo("Sistema operativo personal");
        assertThat(loaded.status()).isSameAs(ProjectStatus.ACTIVE);
        assertThat(loaded.createdAt()).isEqualTo(project.createdAt());
        assertThat(loaded.deletedAt()).isNull();
        assertThat(ids(repo.list(ProjectFilter.all()))).containsExactly(project.id());
    }

    @Test
    void getMissingReturnsEmpty() {
        assertThat(repo.get(UUID.randomUUID())).isEmpty();
    }

    @Test
    void listEmpty() {
        assertThat(repo.list(ProjectFilter.all())).isEmpty();
    }

    @Test
    void listKeepsInsertionOrder() {
        // Sin ORDER BY, igual que Python: los clientes ven el orden de inserción.
        Project a = Project.create("B primero", null);
        Project b = Project.create("A después", null);
        repo.add(a);
        repo.add(b);

        assertThat(ids(repo.list(ProjectFilter.all()))).containsExactly(a.id(), b.id());
    }

    @Test
    void deletedProjectIsInvisibleToGetAndList() {
        Project project = Project.create("Life OS", null);
        repo.add(project);

        project.delete();
        repo.update(project);

        assertThat(repo.get(project.id())).isEmpty();
        assertThat(repo.list(ProjectFilter.all())).isEmpty();
    }

    @Test
    void deletedProjectIsReachableWithIncludeDeleted() {
        Project project = Project.create("Life OS", null);
        repo.add(project);
        project.delete();
        repo.update(project);

        Project loaded = repo.get(project.id(), true).orElseThrow();

        assertThat(loaded.isDeleted()).isTrue();
        assertThat(loaded.deletedAt()).isEqualTo(project.deletedAt());
    }

    @Test
    void updatePersistsRenameStatusAndDescription() {
        Project project = Project.create("Life OS", "original");
        repo.add(project);

        project.rename("Life OS v2");
        project.complete();
        project.describe(null);
        repo.update(project);

        Project reloaded = repo.get(project.id()).orElseThrow();
        assertThat(reloaded.name()).isEqualTo("Life OS v2");
        assertThat(reloaded.status()).isSameAs(ProjectStatus.COMPLETED);
        assertThat(reloaded.description()).isNull();
    }

    @Test
    void listFiltersByStatusAndText() {
        Project casa = Project.create("Casa de campo", null);
        Project finanzas = Project.create("Finanzas", null);
        finanzas.archive();
        repo.add(casa);
        repo.add(finanzas);

        assertThat(ids(repo.list(ProjectFilter.all().withStatuses(List.of(ProjectStatus.ARCHIVED)))))
                .containsExactly(finanzas.id());
        assertThat(ids(repo.list(ProjectFilter.all().matching("CASA")))).containsExactly(casa.id());
    }

    @Test
    void emptyStatusListMatchesNothing() {
        // Igual que `IN ()` en SQLAlchemy: una lista vacía no es "sin filtro".
        repo.add(Project.create("Life OS", null));

        assertThat(repo.list(ProjectFilter.all().withStatuses(List.of()))).isEmpty();
    }

    @Test
    void updateOfAMissingRowFails() {
        // Si otro proceso borró la fila, el UPDATE toca 0 filas: no puede
        // reportarse como éxito.
        var entity = Project.create("Nunca guardado", null);

        assertThatThrownBy(() -> repo.update(entity)).isInstanceOf(ProjectNotFoundException.class);
    }
}
