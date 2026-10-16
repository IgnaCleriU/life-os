package lifeos.domain;

/** Se viola una invariante del dominio (ej. nombre/título vacío). */
public class DomainValidationException extends DomainException {

    public DomainValidationException(String message) {
        super(message);
    }
}
