package lifeos.domain;

/**
 * Base de todas las excepciones de dominio de Life OS.
 *
 * <p>Java puro: no dependen de Spring, SQLite ni MCP. Las capas externas son las
 * encargadas de traducirlas a respuestas HTTP o mensajes para el agente.
 */
public abstract class DomainException extends RuntimeException {

    protected DomainException(String message) {
        super(message);
    }
}
