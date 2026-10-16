package lifeos.adapters.rest;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;

/**
 * La API todavía no tiene autenticación: solo puede escuchar en loopback. En
 * {@code 0.0.0.0} cualquier equipo de la LAN leería y escribiría la base real.
 */
class ServerBindingTest extends RestTestSupport {

    @Value("${server.address:}")
    String serverAddress;

    @Test
    void listensOnLoopbackOnly() {
        assertThat(serverAddress).isEqualTo("127.0.0.1");
    }
}
