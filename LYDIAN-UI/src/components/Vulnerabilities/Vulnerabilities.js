import React, { Component } from 'react'

import { baseUrl } from '../../config';
import axios from 'axios';
import "react-tabulator/lib/styles.css"; // default theme
import "react-tabulator/css/bootstrap/tabulator_bootstrap4.min.css"; // use Theme(s)
<<<<<<< HEAD
import { ReactTabulator } from 'react-tabulator'
=======
import { ReactTabulator, reactFormatter } from 'react-tabulator'
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
import {Container, Row, Col} from 'react-bootstrap'


export class Vulnerabilities extends Component {
    constructor(props) {
        super(props)
    
        this.state = {
            vulnerabilitiesData: []
        }
    }

    componentDidMount() {
        axios.get(baseUrl + 'api/v1/tables/risks')
            .then(response => {
                this.setState({
                    vulnerabilitiesData : response.data
                });
            })
            .catch(function(error) {
                console.log(error);
            })
        }


    render() {
        const columns = [
            { title: "Host", field: "host"},
<<<<<<< HEAD
            {title: "Tool", field: "tool"},
            {title: "Req ID", field: "reqid"},
=======
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
            { title: "Severity", field: "severity"},
            { title: "Message", field: "message"},
          ];
          const options = {
            movableRows: true,
<<<<<<< HEAD
            movableColumns: true,
            pagination:"local",
            paginationSize:10,
=======
            movableColumns: true
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
          };

        return (
            <div>
            <Container>
            <Row className="show-grid">
                <Col md={{ span: 8, offset: 2}}>
                <h1 style={{marginLeft: '350px', fontSize: 26, fontWeight: 'bold', marginBottom: '20px'}}>Vulnerabilites Data</h1>
                <ReactTabulator
                    data={this.state.vulnerabilitiesData}
                    columns={columns}
                    tooltips={true}
                    options={options}
                    style={{border: "2px solid rgb(0, 0, 0)"}}
                    data-custom-attr="test-custom-attribute"
                    className="table-active table-light thead-dark table-striped table-primary table-bordered "          
                    />
                </Col>
                </Row>
            </Container>
            </div>
        )
    }
}

export default Vulnerabilities;
