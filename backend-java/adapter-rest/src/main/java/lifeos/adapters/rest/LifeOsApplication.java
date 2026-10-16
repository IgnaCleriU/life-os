package lifeos.adapters.rest;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Punto de entrada del backend REST de Life OS. */
@SpringBootApplication
public class LifeOsApplication {

    public static void main(String[] args) {
        SpringApplication.run(LifeOsApplication.class, args);
    }
}
