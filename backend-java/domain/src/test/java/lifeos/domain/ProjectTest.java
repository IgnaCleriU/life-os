package lifeos.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.temporal.ChronoUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

/** Tests unitarios de la entidad Project (Java puro, sin DB ni mocks). */
class ProjectTest {

    @Test
    void createGeneratesIdAndTimestamp() {
        Project project = Project.create("Life OS", null);

        assertThat(project.id()).isNotNull();
        assertThat(project.createdAt()).isNotNull();
        assertThat(project.status()).isSameAs(ProjectStatus.ACTIVE);
        assertThat(project.name()).isEqualTo("Life OS");
        assertThat(project.description()).isNull();
    }

    @Test
    void createTruncatesTimestampToMicroseconds() {
        // SQLite guarda microsegundos: un Instant con nanos no sobreviviría
        // a una ida y vuelta por la base sin cambiar.
        Project project = Project.create("Life OS", null);

        assertThat(project.createdAt())
                .isEqualTo(project.createdAt().truncatedTo(ChronoUnit.MICROS));
    }

    @Test
    void createNormalizesName() {
        assertThat(Project.create("  Life OS  ", null).name()).isEqualTo("Life OS");
    }

    @ParameterizedTest
    @ValueSource(strings = {"", "   "})
    void createWithEmptyNameThrows(String invalidName) {
        assertThatThrownBy(() -> Project.create(invalidName, null))
                .isInstanceOf(DomainValidationException.class);
    }

    @Test
    void createWithNullNameThrows() {
        assertThatThrownBy(() -> Project.create(null, null))
                .isInstanceOf(DomainValidationException.class);
    }

    @Test
    void renameChangesName() {
        Project project = Project.create("Viejo", null);

        project.rename("Nuevo");

        assertThat(project.name()).isEqualTo("Nuevo");
    }

    @Test
    void renameWithEmptyNameThrows() {
        Project project = Project.create("Life OS", null);

        assertThatThrownBy(() -> project.rename("   "))
                .isInstanceOf(DomainValidationException.class);
    }

    @Test
    void completeSetsCompletedStatus() {
        Project project = Project.create("Life OS", null);

        project.complete();

        assertThat(project.status()).isSameAs(ProjectStatus.COMPLETED);
    }

    @Test
    void freeTransitionsBetweenStates() {
        Project project = Project.create("Life OS", null);

        project.complete();
        assertThat(project.status()).isSameAs(ProjectStatus.COMPLETED);
        // desde completado se puede reactivar
        project.activate();
        assertThat(project.status()).isSameAs(ProjectStatus.ACTIVE);
        project.archive();
        assertThat(project.status()).isSameAs(ProjectStatus.ARCHIVED);
        // desde archivado se puede volver a completar
        project.complete();
        assertThat(project.status()).isSameAs(ProjectStatus.COMPLETED);
        // y volver a activo
        project.activate();
        assertThat(project.status()).isSameAs(ProjectStatus.ACTIVE);
    }

    @Test
    void describeSetsAndClearsDescription() {
        Project project = Project.create("Life OS", "original");

        project.describe("nueva");
        assertThat(project.description()).isEqualTo("nueva");

        project.describe(null);
        assertThat(project.description()).isNull();
    }

    @Test
    void createIsNotDeleted() {
        Project project = Project.create("Life OS", null);

        assertThat(project.deletedAt()).isNull();
        assertThat(project.isDeleted()).isFalse();
    }

    @Test
    void deleteMarksAndRestoreClears() {
        Project project = Project.create("Life OS", null);

        project.delete();
        assertThat(project.isDeleted()).isTrue();
        assertThat(project.deletedAt()).isNotNull();

        project.restore();
        assertThat(project.isDeleted()).isFalse();
        assertThat(project.deletedAt()).isNull();
    }

    @Test
    void deleteIsIdempotentAndKeepsOriginalTimestamp() {
        Project project = Project.create("Life OS", null);
        project.delete();
        var primeraMarca = project.deletedAt();

        project.delete();

        assertThat(project.deletedAt()).isEqualTo(primeraMarca);
    }

    @Test
    void statusValuesMatchTheStoredStrings() {
        // Los valores en minúscula son los que ya están en la base compartida.
        assertThat(ProjectStatus.ACTIVE.value()).isEqualTo("active");
        assertThat(ProjectStatus.COMPLETED.value()).isEqualTo("completed");
        assertThat(ProjectStatus.ARCHIVED.value()).isEqualTo("archived");
        assertThat(ProjectStatus.fromValue("archived")).isSameAs(ProjectStatus.ARCHIVED);
        assertThatThrownBy(() -> ProjectStatus.fromValue("nope"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
